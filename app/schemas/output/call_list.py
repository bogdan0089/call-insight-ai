from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from app.models.calls import CallStatus


class CallListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None
    operator_id: int | None
    operator_name: str | None = None
    status: CallStatus
    duration_sec: int | None
    total_score: Decimal | None
    created_at: datetime


class CallPage(BaseModel):
    items: list[CallListItem]
    total: int
    limit: int
    offset: int

    @computed_field
    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
