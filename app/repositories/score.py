from collections.abc import Sequence

from sqlalchemy import delete, select

from app.models.scores import CallScore
from app.repositories.base_repository import SqlalchemyAsyncRepository


class CallScoreRepository(SqlalchemyAsyncRepository[CallScore]):
    model = CallScore

    async def get_by_call_id(self, call_id: int) -> Sequence[CallScore]:
        stmt = select(CallScore).where(CallScore.call_id == call_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_call_id(self, call_id: int) -> None:
        await self.session.execute(delete(CallScore).where(CallScore.call_id == call_id))
