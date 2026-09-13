from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.models.users import User
from app.schemas.input.auth import (
    LoginRequest,
    RegisterRequest,
    ResendRequest,
    VerifyRequest,
)
from app.schemas.output.user import (
    OrganizationOut,
    ProfileResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    await service.register(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        organization_name=payload.organization_name,
    )
    return {"detail": "Check your inbox to confirm the address"}


@router.post("/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    payload: ResendRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    await service.resend(email=payload.email)
    return {"detail": "Check your inbox to confirm the address"}


@router.post("/verify", response_model=UserResponse)
async def verify_email(
    payload: VerifyRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.verify(token=payload.token)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user, token, expires_in = await service.login(
        email=payload.email,
        password=payload.password,
    )
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=ProfileResponse)
async def me(
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ProfileResponse:
    user, organization = await service.profile(user)
    return ProfileResponse(
        user=UserResponse.model_validate(user),
        organization=(
            OrganizationOut.model_validate(organization) if organization else None
        ),
    )
