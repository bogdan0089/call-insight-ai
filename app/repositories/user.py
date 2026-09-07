from app.models.users import User
from app.repositories.base_repository import SqlalchemyAsyncRepository


class UserRepository(SqlalchemyAsyncRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by(email=email)
