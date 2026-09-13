from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, Numeric, Row, cast, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.sorting import SortOrder, apply_sort
from app.exceptions import DatabaseError
from app.models.calls import Call
from app.models.checklist import ChecklistItem
from app.models.scores import CallScore
from app.models.users import User
from app.schemas.input.stats import ChecklistSortField, OperatorSortField


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _call_conditions(
        self,
        operator_id: int | None,
        created_from: datetime | None,
        created_to: datetime | None,
        scope: ColumnElement[bool] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if scope is not None:
            conditions.append(scope)
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
        call_scope: ColumnElement[bool] | None,
        operator_scope: ColumnElement[bool] | None,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort_by: OperatorSortField = OperatorSortField.AVG_SCORE,
        order: SortOrder = SortOrder.DESC,
    ) -> Sequence[Row[Any]]:
        failed_required_exists = (
            select(CallScore.id)
            .join(ChecklistItem, ChecklistItem.id == CallScore.checklist_item_id)
            .where(
                CallScore.call_id == Call.id,
                CallScore.passed.is_(False),
                ChecklistItem.is_required.is_(True),
            )
            .exists()
        )

        calls_total = func.count(Call.id)
        calls_scored = func.count(Call.total_score)
        avg_score = func.round(func.avg(Call.total_score), 2)
        min_score = func.min(Call.total_score)
        max_score = func.max(Call.total_score)
        failed_required = func.count(Call.id).filter(failed_required_exists)
        failed_required_rate = cast(failed_required, Numeric) / func.nullif(calls_total, 0)

        columns = {
            OperatorSortField.NAME: func.lower(User.last_name + " " + User.first_name),
            OperatorSortField.CALLS_TOTAL: calls_total,
            OperatorSortField.CALLS_SCORED: calls_scored,
            OperatorSortField.AVG_SCORE: avg_score,
            OperatorSortField.MIN_SCORE: min_score,
            OperatorSortField.MAX_SCORE: max_score,
            OperatorSortField.FAILED_REQUIRED: failed_required,
            OperatorSortField.FAILED_REQUIRED_RATE: failed_required_rate,
        }

        stmt = (
            select(
                User.id.label("operator_id"),
                User.first_name,
                User.last_name,
                calls_total.label("calls_total"),
                calls_scored.label("calls_scored"),
                avg_score.label("avg_score"),
                min_score.label("min_score"),
                max_score.label("max_score"),
                failed_required.label("failed_required"),
            )
            .join(Call, Call.operator_id == User.id)
            .where(
                *self._call_conditions(operator_id, created_from, created_to, call_scope)
            )
            .group_by(User.id)
        )
        if operator_scope is not None:
            stmt = stmt.where(operator_scope)

        return await self._fetch(
            apply_sort(stmt, columns, sort_by, order, tiebreaker=User.id)
        )

    async def daily(
        self,
        call_scope: ColumnElement[bool] | None,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> Sequence[Row[Any]]:
        """Per-day metrics in the reporting timezone."""
        day = func.date(func.timezone(settings.report_timezone, Call.created_at))

        failed_required_exists = (
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
                day.label("day"),
                func.count(Call.id).label("calls_total"),
                func.count(Call.total_score).label("calls_scored"),
                func.round(func.avg(Call.total_score), 2).label("avg_score"),
                func.count(Call.id).filter(failed_required_exists).label("failed_required"),
            )
            .where(
                *self._call_conditions(operator_id, created_from, created_to, call_scope)
            )
            .group_by(day)
            .order_by(day)
        )
        return await self._fetch(stmt)

    async def checklist(
        self,
        call_scope: ColumnElement[bool] | None,
        operator_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort_by: ChecklistSortField = ChecklistSortField.PASS_RATE,
        order: SortOrder = SortOrder.ASC,
    ) -> Sequence[Row[Any]]:
        scored = func.count(CallScore.id)
        passed = func.count(CallScore.id).filter(CallScore.passed.is_(True))
        pass_rate = cast(passed, Numeric) / func.nullif(scored, 0)

        columns = {
            ChecklistSortField.CODE: ChecklistItem.code,
            ChecklistSortField.TITLE: func.lower(ChecklistItem.title),
            ChecklistSortField.WEIGHT: ChecklistItem.weight,
            ChecklistSortField.SCORED: scored,
            ChecklistSortField.PASSED: passed,
            ChecklistSortField.PASS_RATE: pass_rate,
        }

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
            .where(
                *self._call_conditions(operator_id, created_from, created_to, call_scope)
            )
            .group_by(ChecklistItem.id)
        )

        return await self._fetch(
            apply_sort(stmt, columns, sort_by, order, tiebreaker=ChecklistItem.id)
        )
