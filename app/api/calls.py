from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.deps import (
    get_call_service,
    get_current_user,
    get_embedding_service,
    get_score_service,
    require,
)
from app.core.permissions import can_verify_scores
from app.models.users import User
from app.repositories.scope import visible_calls
from app.schemas.input.call_filters import CallListQuery
from app.schemas.input.score import ScoreVerifyRequest
from app.schemas.output.call import CallResponse
from app.schemas.output.call_list import CallListItem, CallPage
from app.schemas.output.report import CallReport, ScoreOut
from app.schemas.output.similar import SimilarCall
from app.services.call import CallService
from app.services.embedding import EmbeddingService
from app.services.score import CallScoreService

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=CallResponse)
async def upload_call(
    file: UploadFile = File(...),
    operator_id: int | None = Form(default=None),
    external_id: str | None = Form(default=None),
    service: CallService = Depends(get_call_service),
    actor: User = Depends(get_current_user),
) -> CallResponse:
    content = await file.read()
    call = await service.create_from_audio(
        actor=actor,
        filename=file.filename or "audio.mp3",
        content=content,
        operator_id=operator_id,
        external_id=external_id,
    )
    return CallResponse.model_validate(call)


@router.get("", response_model=CallPage)
async def list_calls(
    query: Annotated[CallListQuery, Query()],
    service: CallService = Depends(get_call_service),
    actor: User = Depends(get_current_user),
) -> CallPage:
    calls, total = await service.list_calls(
        **query.model_dump(), scope=visible_calls(actor)
    )
    return CallPage(
        items=[CallListItem.model_validate(call) for call in calls],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/search", response_model=list[SimilarCall])
async def search_calls(
    q: str = Query(min_length=2, description="Semantic search over transcripts"),
    limit: int = Query(default=5, ge=1, le=50),
    service: EmbeddingService = Depends(get_embedding_service),
    actor: User = Depends(get_current_user),
) -> list[SimilarCall]:
    return await service.search_calls(query=q, limit=limit, scope=visible_calls(actor))


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    service: CallService = Depends(get_call_service),
    actor: User = Depends(get_current_user),
) -> CallResponse:
    call = await service.get_report(call_id, scope=visible_calls(actor))
    return CallResponse.model_validate(call)


@router.get("/{call_id}/report", response_model=CallReport)
async def get_call_report(
    call_id: int,
    service: CallService = Depends(get_call_service),
    actor: User = Depends(get_current_user),
) -> CallReport:
    call = await service.get_report(call_id, scope=visible_calls(actor))
    return CallReport.from_model(call)


@router.get("/{call_id}/similar", response_model=list[SimilarCall])
async def get_similar_calls(
    call_id: int,
    limit: int = Query(default=5, ge=1, le=50),
    service: EmbeddingService = Depends(get_embedding_service),
    actor: User = Depends(get_current_user),
) -> list[SimilarCall]:
    return await service.find_similar_calls(
        call_id=call_id, limit=limit, scope=visible_calls(actor)
    )


@router.patch("/{call_id}/scores/{score_id}", response_model=ScoreOut)
async def verify_score(
    call_id: int,
    score_id: int,
    payload: ScoreVerifyRequest,
    service: CallScoreService = Depends(get_score_service),
    actor: User = Depends(require(can_verify_scores, "verify scores")),
) -> ScoreOut:
    score = await service.set_verified(
        call_id=call_id,
        score_id=score_id,
        is_verified=payload.is_verified,
        scope=visible_calls(actor),
    )
    return ScoreOut.from_model(score)
