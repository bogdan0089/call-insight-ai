from datetime import datetime

from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats import StatsRepository
from app.schemas.output.stats import ChecklistStats, OperatorStats


class StatsService:
    def __init__(self, repo: StatsRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def operators(
        self,
        call_scope: ColumnElement[bool] | None,
        operator_scope: ColumnElement[bool] | None,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[OperatorStats]:
        rows = await self.repo.operators(
            call_scope=call_scope,
            operator_scope=operator_scope,
            operator_id=operator_id,
            created_from=created_from,
            created_to=created_to,
        )
        return [
            OperatorStats(
                operator_id=row.operator_id,
                operator_name=f"{row.first_name} {row.last_name}",
                calls_total=row.calls_total,
                calls_scored=row.calls_scored,
                avg_score=row.avg_score,
                min_score=row.min_score,
                max_score=row.max_score,
                failed_required=row.failed_required,
            )
            for row in rows
        ]

    async def checklist(
        self,
        call_scope: ColumnElement[bool] | None,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[ChecklistStats]:
        rows = await self.repo.checklist(
            call_scope=call_scope,
            operator_id=operator_id,
            created_from=created_from,
            created_to=created_to,
        )
        return [
            ChecklistStats(
                checklist_item_id=row.checklist_item_id,
                code=row.code,
                title=row.title,
                weight=row.weight,
                is_required=row.is_required,
                scored=row.scored,
                passed=row.passed,
            )
            for row in rows
        ]
