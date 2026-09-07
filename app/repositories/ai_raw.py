from app.models.ai_raw import RawAIResponse
from app.repositories.base_repository import SqlalchemyAsyncRepository


class RawAIResponseRepository(SqlalchemyAsyncRepository[RawAIResponse]):
    model = RawAIResponse
