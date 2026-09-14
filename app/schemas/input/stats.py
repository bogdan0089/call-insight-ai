from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.core.sorting import SortOrder


class OperatorSortField(StrEnum):
    NAME = "operator_name"
    CALLS_TOTAL = "calls_total"
    CALLS_SCORED = "calls_scored"
    AVG_SCORE = "avg_score"
    MIN_SCORE = "min_score"
    MAX_SCORE = "max_score"
    FAILED_REQUIRED = "failed_required"
    FAILED_REQUIRED_RATE = "failed_required_rate"


class ChecklistSortField(StrEnum):
    CODE = "code"
    TITLE = "title"
    WEIGHT = "weight"
    SCORED = "scored"
    PASSED = "passed"
    PASS_RATE = "pass_rate"


class StatsQuery(BaseModel):
    operator_id: int | None = Field(default=None, ge=1)
    created_from: datetime | None = None
    created_to: datetime | None = None

    @model_validator(mode="after")
    def check_range(self) -> "StatsQuery":
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            raise ValueError("created_from must not be later than created_to")
        return self


class OperatorStatsQuery(StatsQuery):
    sort_by: OperatorSortField = OperatorSortField.AVG_SCORE
    order: SortOrder = SortOrder.DESC


class ChecklistStatsQuery(StatsQuery):
    sort_by: ChecklistSortField = ChecklistSortField.PASS_RATE
    order: SortOrder = SortOrder.ASC
