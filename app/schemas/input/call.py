from pydantic import BaseModel, Field


class CallCreateRequest(BaseModel):
    external_id: str | None = Field(default=None, max_length=128)
    operator_id: int | None = None
