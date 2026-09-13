from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.exceptions import DatabaseError
from app.models.calls import Call, CallStatus
from app.models.scores import CallScore
from app.models.transcripts import Transcript
from app.repositories.base_repository import SqlalchemyAsyncRepository


class CallRepository(SqlalchemyAsyncRepository[Call]):
    model = Call

    async def get_by_external_id(self, external_id: str) -> Call | None:
        return await self.get_by(external_id=external_id)

    async def list_calls(
        self,
        operator_id: int | None = None,
        status: CallStatus | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        score_min: Decimal | None = None,
        score_max: Decimal | None = None,
        limit: int = 20,
        offset: int = 0,
        scope: ColumnElement[bool] | None = None,
    ) -> tuple[Sequence[Call], int]:
        conditions: list[ColumnElement[bool]] = []
        if scope is not None:
            conditions.append(scope)
        if operator_id is not None:
            conditions.append(Call.operator_id == operator_id)
        if status is not None:
            conditions.append(Call.status == status)
        if created_from is not None:
            conditions.append(Call.created_at >= created_from)
        if created_to is not None:
            conditions.append(Call.created_at <= created_to)
        if score_min is not None:
            conditions.append(Call.total_score >= score_min)
        if score_max is not None:
            conditions.append(Call.total_score <= score_max)

        rows_stmt = (
            select(Call)
            .where(*conditions)
            .options(selectinload(Call.operator))
            .order_by(Call.created_at.desc(), Call.id.desc())
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(Call).where(*conditions)

        try:
            rows = await self.session.execute(rows_stmt)
            total = await self.session.execute(total_stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc

        return rows.scalars().all(), total.scalar_one()

    async def get_report(
        self,
        call_id: int,
        scope: ColumnElement[bool] | None = None,
    ) -> Call | None:
        conditions: list[ColumnElement[bool]] = [Call.id == call_id]
        if scope is not None:
            conditions.append(scope)

        stmt = (
            select(Call)
            .where(*conditions)
            .options(
                selectinload(Call.operator),
                selectinload(Call.transcript).selectinload(Transcript.segments),
                selectinload(Call.scores).selectinload(CallScore.item),
            )
        )
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc
        return result.scalar_one_or_none()
