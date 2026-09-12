from decimal import Decimal

from pydantic import BaseModel, computed_field


class OperatorStats(BaseModel):
    operator_id: int
    operator_name: str
    calls_total: int
    calls_scored: int
    avg_score: Decimal | None
    min_score: Decimal | None
    max_score: Decimal | None
    failed_required: int

    @computed_field
    @property
    def failed_required_rate(self) -> float | None:
        if self.calls_total == 0:
            return None
        return round(self.failed_required / self.calls_total, 4)


class ChecklistStats(BaseModel):
    checklist_item_id: int
    code: str
    title: str
    weight: Decimal
    is_required: bool
    scored: int
    passed: int

    @computed_field
    @property
    def pass_rate(self) -> float | None:
        if self.scored == 0:
            return None
        return round(self.passed / self.scored, 4)
