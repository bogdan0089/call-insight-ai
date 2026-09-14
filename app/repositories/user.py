from sqlalchemy import ColumnElement, select

from app.models.users import User
from app.repositories.base_repository import SqlalchemyAsyncRepository


class UserRepository(SqlalchemyAsyncRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by(email=email)

    async def get_in_scope(
        self,
        user_id: int,
        scope: "ColumnElement[bool] | None" = None,
    ) -> User | None:
        conditions = [User.id == user_id]
        if scope is not None:
            conditions.append(scope)

        result = await self.session.execute(select(User).where(*conditions))
        return result.scalar_one_or_none()
