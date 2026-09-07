from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.calls import Call, CallStatus
from app.models.scores import CallScore
from app.models.transcripts import Transcript
from app.repositories.base_repository import SqlalchemyAsyncRepository


class TranscriptRepository(SqlalchemyAsyncRepository[Transcript]):
    model = Transcript

    async def get_by_call_id(self, call_id: int) -> Transcript | None:
        return await self.get_by(call_id=call_id)

    async def find_similar(
        self,
        embedding: list[float],
        embedding_model: str,
        exclude_call_id: int | None = None,
        limit: int = 5,
    ) -> Sequence[tuple[Transcript, float]]:
        distance = Transcript.embedding.cosine_distance(embedding)

        stmt = (
            select(Transcript, distance.label("distance"))
            .where(
                Transcript.embedding.is_not(None),
                Transcript.embedding_model == embedding_model,
            )
            .order_by(distance)
            .limit(limit)
        )
        if exclude_call_id is not None:
            stmt = stmt.where(Transcript.call_id != exclude_call_id)

        result = await self.session.execute(stmt)
        return [(row.Transcript, float(row.distance)) for row in result]

    async def find_similar_scored(
        self,
        embedding: list[float],
        embedding_model: str,
        exclude_call_id: int | None = None,
        limit: int = 3,
    ) -> Sequence[tuple[Transcript, float]]:
        distance = Transcript.embedding.cosine_distance(embedding)

        has_verified_scores = (
            select(CallScore.id)
            .where(
                CallScore.call_id == Transcript.call_id,
                CallScore.is_verified.is_(True),
            )
            .exists()
        )

        stmt = (
            select(Transcript, distance.label("distance"))
            .join(Call, Call.id == Transcript.call_id)
            .where(
                Transcript.embedding.is_not(None),
                Transcript.embedding_model == embedding_model,
                Call.status == CallStatus.DONE,
                has_verified_scores,
            )
            .options(
                selectinload(Transcript.call)
                .selectinload(Call.scores)
                .selectinload(CallScore.item)
            )
            .order_by(distance)
            .limit(limit)
        )
        if exclude_call_id is not None:
            stmt = stmt.where(Transcript.call_id != exclude_call_id)

        result = await self.session.execute(stmt)
        return [(row.Transcript, float(row.distance)) for row in result]
