from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EntityNotFound
from app.integrations.embeddings.client import Embedder
from app.models.transcripts import Transcript
from app.repositories.transcript import TranscriptRepository


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
