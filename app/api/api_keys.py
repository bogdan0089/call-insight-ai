from fastapi import APIRouter, Depends, status

from app.api.deps import get_api_key_service, require
from app.core.permissions import can_manage_api_keys
from app.models.users import User
from app.schemas.input.api_key import ApiKeyCreate
from app.schemas.output.api_key import ApiKeyCreated, ApiKeyOut
from app.services.api_key import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["api keys"])

Owner = Depends(require(can_manage_api_keys, "manage api keys"))


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    service: ApiKeyService = Depends(get_api_key_service),
    actor: User = Owner,
) -> list[ApiKeyOut]:
    keys = await service.list_keys(actor)
    return [ApiKeyOut.model_validate(key) for key in keys]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiKeyCreated)
async def create_api_key(
    payload: ApiKeyCreate,
    service: ApiKeyService = Depends(get_api_key_service),
    actor: User = Owner,
) -> ApiKeyCreated:
    key, secret = await service.create(actor=actor, name=payload.name)
    return ApiKeyCreated(key=ApiKeyOut.model_validate(key), secret=secret)


@router.delete("/{key_id}", response_model=ApiKeyOut)
async def revoke_api_key(
    key_id: int,
    service: ApiKeyService = Depends(get_api_key_service),
    actor: User = Owner,
) -> ApiKeyOut:
    key = await service.revoke(actor=actor, key_id=key_id)
    return ApiKeyOut.model_validate(key)
