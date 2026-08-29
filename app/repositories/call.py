from app.models.calls import Call
from app.repositories.base_repository import SqlalchemyAsyncRepository


class CallRepository(SqlalchemyAsyncRepository[Call]):
    model = Call

    async def get_by_external_id(self, external_id: str) -> Call | None:
        return await self.get_by(external_id=external_id)
