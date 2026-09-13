from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.api.rate_limit import enforce, limit_by_ip
from app.core.permissions import is_demo
from app.models.users import User
from app.schemas.input.auth import (
    AcceptInviteRequest,
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


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(limit_by_ip("register"))],
)
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


@router.post(
    "/resend",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(limit_by_ip("resend"))],
)
async def resend_verification(
    payload: ResendRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    await service.resend(email=payload.email)
    return {"detail": "Check your inbox to confirm the address"}


@router.post(
    "/verify",
    response_model=UserResponse,
    dependencies=[Depends(limit_by_ip("verify"))],
)
async def verify_email(
    payload: VerifyRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.verify(token=payload.token)
    return UserResponse.model_validate(user)


@router.post(
    "/accept-invite",
    response_model=UserResponse,
    dependencies=[Depends(limit_by_ip("verify"))],
)
async def accept_invitation(
    payload: AcceptInviteRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await service.accept_invitation(
        token=payload.token, password=payload.password
    )
    return UserResponse.model_validate(user)


@router.post(
    "/demo",
    response_model=TokenResponse,
    dependencies=[Depends(limit_by_ip("demo"))],
)
async def demo_login(service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    user, token, expires_in = await service.demo_login()
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(limit_by_ip("login_ip"))],
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    await enforce("login_email", payload.email.lower())
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
        is_demo=is_demo(user),
        user=UserResponse.model_validate(user),
        organization=(
            OrganizationOut.model_validate(organization) if organization else None
        ),
    )
