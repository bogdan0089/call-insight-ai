from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.calls import CallStatus


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None
    operator_id: int | None
    status: CallStatus
    duration_sec: int | None
    total_score: Decimal | None
    created_at: datetime
