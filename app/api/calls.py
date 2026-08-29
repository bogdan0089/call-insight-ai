from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import get_call_service
from app.schemas.output.call import CallResponse
from app.services.call import CallService

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


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    service: CallService = Depends(get_call_service),
) -> CallResponse:
    call = await service.get_or_404(call_id)
    return CallResponse.model_validate(call)
