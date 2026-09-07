from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EntityNotFound
from app.integrations.embeddings.client import Embedder
from app.models.transcripts import Transcript
from app.repositories.transcript import TranscriptRepository
from app.schemas.output.similar import SimilarCall

EXCERPT_CHARS = 200


class EmbeddingService:
    def __init__(self, session: AsyncSession, embedder: Embedder) -> None:
        self.session = session
        self.embedder = embedder
        self.transcripts = TranscriptRepository(session)

    async def embed_transcript(self, call_id: int) -> Transcript:
        transcript = await self.transcripts.get_by_call_id(call_id)
        if transcript is None:
            raise EntityNotFound(entity="Transcript", call_id=call_id)

        if transcript.embedding_model == self.embedder.model_name:
            return transcript

        transcript.embedding = await self.embedder.embed(transcript.text)
        transcript.embedding_model = self.embedder.model_name
        await self.session.commit()
        return transcript

    async def find_similar_calls(self, call_id: int, limit: int = 5) -> list[SimilarCall]:
        transcript = await self.transcripts.get_by_call_id(call_id)
        if transcript is None:
            raise EntityNotFound(entity="Transcript", call_id=call_id)
        if transcript.embedding is None:
            return []

        rows = await self.transcripts.find_similar(
            embedding=transcript.embedding,
            embedding_model=transcript.embedding_model or self.embedder.model_name,
            exclude_call_id=call_id,
            limit=limit,
        )
        return self._to_similar(rows)

    async def search_calls(self, query: str, limit: int = 5) -> list[SimilarCall]:
        embedding = await self.embedder.embed(query)

        rows = await self.transcripts.find_similar(
            embedding=embedding,
            embedding_model=self.embedder.model_name,
            limit=limit,
        )
        return self._to_similar(rows)

    @staticmethod
    def _to_similar(rows: Sequence[tuple[Transcript, float]]) -> list[SimilarCall]:
        return [
            SimilarCall(
                call_id=found.call_id,
                similarity=round(1 - distance, 4),
                excerpt=found.text[:EXCERPT_CHARS],
            )
            for found, distance in rows
        ]
