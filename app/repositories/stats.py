from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, Row, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DatabaseError
from app.models.calls import Call
from app.models.checklist import ChecklistItem
from app.models.scores import CallScore
from app.models.users import User


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _call_conditions(
        self,
        operator_id: int | None,
        created_from: datetime | None,
        created_to: datetime | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if operator_id is not None:
            conditions.append(Call.operator_id == operator_id)
        if created_from is not None:
            conditions.append(Call.created_at >= created_from)
        if created_to is not None:
            conditions.append(Call.created_at <= created_to)
        return conditions

    async def _fetch(self, stmt: Any) -> Sequence[Row[Any]]:
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc
        return result.all()

    async def operators(
        self,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> Sequence[Row[Any]]:
        failed_required = (
            select(CallScore.id)
            .join(ChecklistItem, ChecklistItem.id == CallScore.checklist_item_id)
            .where(
                CallScore.call_id == Call.id,
                CallScore.passed.is_(False),
                ChecklistItem.is_required.is_(True),
            )
            .exists()
        )

        stmt = (
            select(
                User.id.label("operator_id"),
                User.first_name,
                User.last_name,
                func.count(Call.id).label("calls_total"),
                func.count(Call.total_score).label("calls_scored"),
                func.round(func.avg(Call.total_score), 2).label("avg_score"),
                func.min(Call.total_score).label("min_score"),
                func.max(Call.total_score).label("max_score"),
                func.count(Call.id).filter(failed_required).label("failed_required"),
            )
            .join(Call, Call.operator_id == User.id)
            .where(*self._call_conditions(operator_id, created_from, created_to))
            .group_by(User.id)
            .order_by(func.avg(Call.total_score).desc().nullslast())
        )
        return await self._fetch(stmt)

    async def checklist(
        self,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> Sequence[Row[Any]]:
        scored = func.count(CallScore.id)
        passed = func.count(CallScore.id).filter(CallScore.passed.is_(True))

        stmt = (
            select(
                ChecklistItem.id.label("checklist_item_id"),
                ChecklistItem.code,
                ChecklistItem.title,
                ChecklistItem.weight,
                ChecklistItem.is_required,
                scored.label("scored"),
                passed.label("passed"),
            )
            .join(CallScore, CallScore.checklist_item_id == ChecklistItem.id)
            .join(Call, Call.id == CallScore.call_id)
            .where(*self._call_conditions(operator_id, created_from, created_to))
            .group_by(ChecklistItem.id)
            .order_by((passed * 1.0 / func.nullif(scored, 0)).asc().nullslast())
        )
        return await self._fetch(stmt)
