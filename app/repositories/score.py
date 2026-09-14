from collections.abc import Sequence

from sqlalchemy import ColumnElement, delete, select
from sqlalchemy.orm import selectinload

from app.models.calls import Call
from app.models.scores import CallScore
from app.repositories.base_repository import SqlalchemyAsyncRepository


class CallScoreRepository(SqlalchemyAsyncRepository[CallScore]):
    model = CallScore

    async def get_by_call_id(self, call_id: int) -> Sequence[CallScore]:
        stmt = select(CallScore).where(CallScore.call_id == call_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_call(
        self,
        call_id: int,
        score_id: int,
        scope: ColumnElement[bool] | None = None,
    ) -> CallScore | None:
        stmt = (
            select(CallScore)
            .where(CallScore.id == score_id, CallScore.call_id == call_id)
            .options(selectinload(CallScore.item))
        )
        if scope is not None:
            stmt = stmt.join(Call, Call.id == CallScore.call_id).where(scope)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_call_id(self, call_id: int) -> None:
        await self.session.execute(delete(CallScore).where(CallScore.call_id == call_id))
