from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.core.limits import (
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MAX,
    SCORE_MAX,
    SCORE_MIN,
)
from app.core.sorting import SortOrder
from app.models.calls import CallStatus


class CallSortField(StrEnum):
    CREATED_AT = "created_at"
    OPERATOR = "operator"
    TOTAL_SCORE = "total_score"
    DURATION = "duration_sec"
    STATUS = "status"


class CallListQuery(BaseModel):
    operator_id: int | None = Field(default=None, ge=1)
    status: CallStatus | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    score_min: Decimal | None = Field(default=None, ge=SCORE_MIN, le=SCORE_MAX)
    score_max: Decimal | None = Field(default=None, ge=SCORE_MIN, le=SCORE_MAX)
    limit: int = Field(default=PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX)
    offset: int = Field(default=0, ge=0)
    sort_by: CallSortField = CallSortField.CREATED_AT
    order: SortOrder = SortOrder.DESC

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
