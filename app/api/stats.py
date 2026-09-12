from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_stats_service
from app.schemas.input.stats import StatsQuery
from app.schemas.output.stats import ChecklistStats, OperatorStats
from app.services.stats import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/operators", response_model=list[OperatorStats])
async def operator_stats(
    query: Annotated[StatsQuery, Query()],
    service: StatsService = Depends(get_stats_service),
) -> list[OperatorStats]:
    return await service.operators(**query.model_dump())


@router.get("/checklist", response_model=list[ChecklistStats])
async def checklist_stats(
    query: Annotated[StatsQuery, Query()],
    service: StatsService = Depends(get_stats_service),
) -> list[ChecklistStats]:
    return await service.checklist(**query.model_dump())
