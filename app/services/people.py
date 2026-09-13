from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.permissions import sees_whole_org
from app.exceptions import AlreadyExistsError, EntityNotFound, PermissionDenied
from app.models.users import User, UserRole
from app.repositories.organization import OrganizationRepository
from app.repositories.people import PeopleRepository
from app.repositories.scope import visible_operators
from app.services.invitation import InvitationService

logger = get_logger(__name__)


class PeopleService:
    """Team management within one organization."""

    def __init__(
        self,
        session: AsyncSession,
        repo: PeopleRepository,
        organizations: OrganizationRepository,
        invitations: InvitationService,
    ) -> None:
        self.session = session
        self.repo = repo
        self.organizations = organizations
        self.invitations = invitations

    async def list_people(
        self,
        actor: User,
        role: UserRole | None = None,
        manager_id: int | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[User], int]:
        return await self.repo.list_people(
            scope=visible_operators(actor),
            role=role,
            manager_id=manager_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

    async def invite(
        self,
        actor: User,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        manager_id: int | None,
    ) -> User:
        email = email.lower()
        if await self.repo.get_by(email=email) is not None:
            raise AlreadyExistsError(constraint="email")

        role, manager_id = self._resolve_placement(actor, role, manager_id)
        await self._check_manager_exists(actor, manager_id)

        person = await self.repo.create(
            User(
                email=email,
                hashed_password="",
                first_name=first_name,
                last_name=last_name,
                role=role,
                organization_id=actor.organization_id,
                manager_id=manager_id,
            )
        )
        organization = await self.organizations.get(actor.organization_id)
        await self.invitations.send(
            person, organization.name if organization else "call insight"
        )
        await self.session.commit()
        logger.info(
            "person invited | by=%s user=%s role=%s manager=%s",
            actor.id,
            person.id,
            person.role.value,
            person.manager_id,
        )

        return await self.repo.get_in_scope(person.id, visible_operators(actor)) or person

    async def update(
        self,
        actor: User,
        person_id: int,
        role: UserRole | None,
        manager_id: int | None,
        is_active: bool | None,
    ) -> User:
        person = await self.repo.get_in_scope(person_id, visible_operators(actor))
        if person is None:
            raise EntityNotFound(entity="User", id=person_id)
        if person.id == actor.id:
            raise PermissionDenied("change your own access")
        if not sees_whole_org(actor) and role is not None:
            raise PermissionDenied("change roles")

        if role is not None:
            person.role = role
        if manager_id is not None:
            await self._check_manager_exists(actor, manager_id)
            person.manager_id = manager_id
        if is_active is not None:
            person.is_active = is_active

        await self.session.commit()
        logger.info("person updated | by=%s user=%s", actor.id, person.id)
        return person

    def _resolve_placement(
        self,
        actor: User,
        role: UserRole,
        manager_id: int | None,
    ) -> tuple[UserRole, int | None]:
        """Managers may invite only operators, under themselves."""
        if sees_whole_org(actor):
            return role, manager_id

        if role is not UserRole.OPERATOR:
            raise PermissionDenied("invite this role")
        if manager_id not in (None, actor.id):
            raise PermissionDenied("assign another manager")

        return UserRole.OPERATOR, actor.id

    async def _check_manager_exists(self, actor: User, manager_id: int | None) -> None:
        if manager_id is None:
            return

        manager = await self.repo.get_in_scope(manager_id, visible_operators(actor))
        if manager is None:
            raise EntityNotFound(entity="User", id=manager_id)
