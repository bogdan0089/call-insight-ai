from app.models.transcripts import Transcript
from app.repositories.base_repository import SqlalchemyAsyncRepository


class TranscriptRepository(SqlalchemyAsyncRepository[Transcript]):
    model = Transcript

    async def get_by_call_id(self, call_id: int) -> Transcript | None:
        return await self.get_by(call_id=call_id)
