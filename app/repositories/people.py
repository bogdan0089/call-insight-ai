from collections.abc import Sequence

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.core.permissions import ROLE_RANK
from app.core.sorting import SortOrder, apply_sort
from app.exceptions import DatabaseError
from app.models.organizations import ApiKey
from app.models.users import User, UserRole
from app.repositories.base_repository import SqlalchemyAsyncRepository
from app.schemas.input.people import PeopleSortField

SORT_COLUMNS = {
    PeopleSortField.NAME: func.lower(User.last_name + ' ' + User.first_name),
    PeopleSortField.EMAIL: User.email,
    PeopleSortField.ROLE: case(
        {role: rank for role, rank in ROLE_RANK.items()}, value=User.role
    ),
    PeopleSortField.CREATED_AT: User.created_at,
}


def is_person() -> ColumnElement[bool]:
    """Exclude service users that back API keys."""
    return ~select(ApiKey.id).where(ApiKey.user_id == User.id).exists()


class PeopleRepository(SqlalchemyAsyncRepository[User]):
    model = User

    async def list_people(
        self,
        scope: ColumnElement[bool] | None = None,
        role: UserRole | None = None,
        manager_id: int | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: PeopleSortField = PeopleSortField.NAME,
        order: SortOrder = SortOrder.ASC,
    ) -> tuple[Sequence[User], int]:
        conditions: list[ColumnElement[bool]] = [is_person()]
        if scope is not None:
            conditions.append(scope)
        if role is not None:
            conditions.append(User.role == role)
        if manager_id is not None:
            conditions.append(User.manager_id == manager_id)
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))

        rows_stmt = apply_sort(
            select(User).where(*conditions).options(selectinload(User.manager)),
            SORT_COLUMNS,
            sort_by,
            order,
            tiebreaker=User.id,
        ).limit(limit).offset(offset)
        total_stmt = select(func.count()).select_from(User).where(*conditions)

        try:
            rows = await self.session.execute(rows_stmt)
            total = await self.session.execute(total_stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc

        return rows.scalars().all(), total.scalar_one()

    async def get_in_scope(
        self,
        user_id: int,
        scope: ColumnElement[bool] | None = None,
    ) -> User | None:
        conditions: list[ColumnElement[bool]] = [User.id == user_id, is_person()]
        if scope is not None:
            conditions.append(scope)

        stmt = select(User).where(*conditions).options(selectinload(User.manager))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
