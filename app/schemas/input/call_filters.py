from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.calls import CallStatus


class CallListQuery(BaseModel):
    operator_id: int | None = Field(default=None, ge=1)
    status: CallStatus | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    score_min: Decimal | None = Field(default=None, ge=0, le=100)
    score_max: Decimal | None = Field(default=None, ge=0, le=100)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_ranges(self) -> "CallListQuery":
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            raise ValueError("created_from must not be later than created_to")
        if (
            self.score_min is not None
            and self.score_max is not None
            and self.score_min > self.score_max
        ):
            raise ValueError("score_min must not be greater than score_max")
        return self
