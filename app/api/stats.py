from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_stats_service
from app.models.users import User
from app.repositories.scope import visible_calls, visible_operators
from app.schemas.input.stats import StatsQuery
from app.schemas.output.stats import ChecklistStats, OperatorStats
from app.services.stats import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/operators", response_model=list[OperatorStats])
async def operator_stats(
    query: Annotated[StatsQuery, Query()],
    service: StatsService = Depends(get_stats_service),
    actor: User = Depends(get_current_user),
) -> list[OperatorStats]:
    return await service.operators(
        call_scope=visible_calls(actor),
        operator_scope=visible_operators(actor),
        **query.model_dump(),
    )


@router.get("/checklist", response_model=list[ChecklistStats])
async def checklist_stats(
    query: Annotated[StatsQuery, Query()],
    service: StatsService = Depends(get_stats_service),
    actor: User = Depends(get_current_user),
) -> list[ChecklistStats]:
    return await service.checklist(call_scope=visible_calls(actor), **query.model_dump())
