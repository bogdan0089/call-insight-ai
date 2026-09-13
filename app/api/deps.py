from collections.abc import Awaitable, Callable

from fastapi import Depends
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rate_limit import enforce
from app.core.db import get_session
from app.core.security import decode_access_token
from app.exceptions import AccountDisabled, NotAuthenticated, PermissionDenied
from app.integrations.embeddings.client import build_embedder
from app.integrations.mail.client import build_mailer
from app.models.users import User
from app.repositories.api_key import ApiKeyRepository
from app.repositories.call import CallRepository
from app.repositories.checklist import ChecklistRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.people import PeopleRepository
from app.repositories.score import CallScoreRepository
from app.repositories.stats import StatsRepository
from app.repositories.user import UserRepository
from app.repositories.verification import EmailVerificationRepository
from app.services.api_key import ApiKeyService
from app.services.auth import AuthService
from app.services.call import CallService
from app.services.embedding import EmbeddingService
from app.services.invitation import InvitationService
from app.services.people import PeopleService
from app.services.score import CallScoreService
from app.services.stats import StatsService


def get_call_service(session: AsyncSession = Depends(get_session)) -> CallService:
    return CallService(repo=CallRepository(session), session=session)


def get_embedding_service(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingService:
    return EmbeddingService(session=session, embedder=build_embedder())


def get_score_service(session: AsyncSession = Depends(get_session)) -> CallScoreService:
    return CallScoreService(repo=CallScoreRepository(session), session=session)


def get_stats_service(session: AsyncSession = Depends(get_session)) -> StatsService:
    return StatsService(repo=StatsRepository(session), session=session)


def get_invitation_service(session: AsyncSession) -> InvitationService:
    return InvitationService(
        session=session,
        verifications=EmailVerificationRepository(session),
        mailer=build_mailer(),
    )


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(
        session=session,
        users=UserRepository(session),
        organizations=OrganizationRepository(session),
        checklist=ChecklistRepository(session),
        verifications=EmailVerificationRepository(session),
        invitations=get_invitation_service(session),
    )


def get_people_service(session: AsyncSession = Depends(get_session)) -> PeopleService:
    return PeopleService(
        session=session,
        repo=PeopleRepository(session),
        organizations=OrganizationRepository(session),
        invitations=get_invitation_service(session),
    )


def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    return ApiKeyService(
        session=session,
        repo=ApiKeyRepository(session),
        users=UserRepository(session),
    )


bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    api_key: str | None = Depends(api_key_header),
    session: AsyncSession = Depends(get_session),
) -> User:
    if api_key:
        service = ApiKeyService(
            session=session,
            repo=ApiKeyRepository(session),
            users=UserRepository(session),
        )
        user = await service.authenticate(api_key)
        if user is None:
            raise NotAuthenticated("Invalid API key")
        await enforce("principal", f"user:{user.id}")
        return user

    if credentials is None:
        raise NotAuthenticated

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (PyJWTError, KeyError, ValueError) as exc:
        raise NotAuthenticated("Invalid or expired token") from exc

    user = await UserRepository(session).get(user_id)
    if user is None:
        raise NotAuthenticated("Invalid or expired token")
    if not user.is_active:
        raise AccountDisabled

    await enforce("principal", f"user:{user.id}")
    return user


def require(rule: Callable[[User], bool], action: str) -> Callable[..., Awaitable[User]]:
    """Guard an endpoint with a rule from app.core.permissions."""

    async def guard(user: User = Depends(get_current_user)) -> User:
        if not rule(user):
            raise PermissionDenied(action)
        return user

    return guard
