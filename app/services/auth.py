from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.limits import ORG_SLUG_MAX
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.slug import slugify, unique_slug
from app.exceptions import (
    AccountDisabled,
    EmailNotVerified,
    InvalidCredentials,
    InvalidVerificationToken,
)
from app.fixtures.checklist import CHECKLIST
from app.models.organizations import Organization
from app.models.users import User, UserRole
from app.repositories.checklist import ChecklistRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.verification import EmailVerificationRepository
from app.services.invitation import InvitationService

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        organizations: OrganizationRepository,
        checklist: ChecklistRepository,
        verifications: EmailVerificationRepository,
        invitations: InvitationService,
    ) -> None:
        self.session = session
        self.users = users
        self.organizations = organizations
        self.checklist = checklist
        self.verifications = verifications
        self.invitations = invitations

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        organization_name: str,
    ) -> None:
        email = email.lower()
        existing = await self.users.get_by_email(email)

        if existing is not None:
            if not existing.is_verified and existing.is_active:
                await self.invitations.send_verification(existing)
                await self.session.commit()
            return

        organization = await self._create_organization(organization_name)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.OWNER,
            organization_id=organization.id,
        )
        await self.users.create(user)
        await self._add_starter_checklist(organization.id)
        await self.invitations.send_verification(user)
        await self.session.commit()
        logger.info(
            "organization registered | org=%s slug=%s owner=%s",
            organization.id,
            organization.slug,
            user.id,
        )

    async def _create_organization(self, name: str) -> Organization:
        base = slugify(name, ORG_SLUG_MAX)
        taken = await self.organizations.taken_slugs(base or "org")
        slug = unique_slug(base, taken, ORG_SLUG_MAX)
        return await self.organizations.create(Organization(name=name, slug=slug))

    async def _add_starter_checklist(self, organization_id: int) -> None:
        await self.checklist.add_many(organization_id, CHECKLIST)

    async def resend(self, email: str) -> None:
        user = await self.users.get_by_email(email.lower())
        if user is None or user.is_verified or not user.is_active:
            return

        await self.verifications.invalidate_for_user(user.id)
        await self.invitations.send_verification(user)
        await self.session.commit()

    async def verify(self, token: str) -> User:
        record = await self.verifications.get_pending(hash_token(token))
        if record is None:
            raise InvalidVerificationToken

        now = datetime.now(UTC)
        record.used_at = now
        if record.user.email_verified_at is None:
            record.user.email_verified_at = now

        await self.session.commit()
        return record.user

    async def accept_invitation(self, token: str, password: str) -> User:
        """Set the invited user's password and verify their email."""
        record = await self.verifications.get_pending(hash_token(token))
        if record is None:
            raise InvalidVerificationToken

        now = datetime.now(UTC)
        record.used_at = now
        record.user.hashed_password = hash_password(password)
        if record.user.email_verified_at is None:
            record.user.email_verified_at = now

        await self.session.commit()
        logger.info("invitation accepted | user=%s", record.user.id)
        return record.user

    async def profile(self, user: User) -> tuple[User, Organization | None]:
        if user.organization_id is None:
            return user, None
        return user, await self.organizations.get(user.organization_id)

    async def login(self, email: str, password: str) -> tuple[User, str, int]:
        user = await self.users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.hashed_password):
            logger.warning("login refused | email=%s reason=credentials", email)
            raise InvalidCredentials
        if not user.is_active:
            raise AccountDisabled
        if not user.is_verified:
            raise EmailNotVerified

        token = create_access_token(user_id=user.id, role=user.role.value)
        logger.info("login | user=%s org=%s", user.id, user.organization_id)
        return user, token, settings.jwt_ttl_minutes * 60

