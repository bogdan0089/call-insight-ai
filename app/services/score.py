from sqlalchemy import ColumnElement

from app.exceptions import EntityNotFound
from app.models.scores import CallScore
from app.repositories.score import CallScoreRepository
from app.services.base_service import BaseService


class CallScoreService(BaseService[CallScore, CallScoreRepository]):
    entity_name = "CallScore"

    async def set_verified(
        self,
        call_id: int,
        score_id: int,
        is_verified: bool,
        scope: ColumnElement[bool] | None = None,
    ) -> CallScore:
        score = await self.repo.get_for_call(
            call_id=call_id, score_id=score_id, scope=scope
        )
        if score is None:
            raise EntityNotFound(entity=self.entity_name, id=score_id)

        if score.is_verified != is_verified:
            score.is_verified = is_verified
            await self.session.commit()

        return score
