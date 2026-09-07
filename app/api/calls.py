from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.deps import get_call_service, get_embedding_service
from app.schemas.output.call import CallResponse
from app.schemas.output.similar import SimilarCall
from app.services.call import CallService
from app.services.embedding import EmbeddingService

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=CallResponse)
async def upload_call(
    file: UploadFile = File(...),
    operator_id: int | None = Form(default=None),
    external_id: str | None = Form(default=None),
    service: CallService = Depends(get_call_service),
) -> CallResponse:
    content = await file.read()
    call = await service.create_from_audio(
        filename=file.filename or "audio.mp3",
        content=content,
        operator_id=operator_id,
        external_id=external_id,
    )
    return CallResponse.model_validate(call)


@router.get("/search", response_model=list[SimilarCall])
async def search_calls(
    q: str = Query(min_length=2, description="Пошук за змістом розмови"),
    limit: int = Query(default=5, ge=1, le=50),
    service: EmbeddingService = Depends(get_embedding_service),
) -> list[SimilarCall]:
    return await service.search_calls(query=q, limit=limit)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    service: CallService = Depends(get_call_service),
) -> CallResponse:
    call = await service.get_or_404(call_id)
    return CallResponse.model_validate(call)


@router.get("/{call_id}/similar", response_model=list[SimilarCall])
async def get_similar_calls(
    call_id: int,
    limit: int = Query(default=5, ge=1, le=50),
    service: EmbeddingService = Depends(get_embedding_service),
) -> list[SimilarCall]:
    return await service.find_similar_calls(call_id=call_id, limit=limit)
