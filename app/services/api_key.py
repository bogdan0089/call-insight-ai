from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.limits import API_KEY_PREFIX_LEN
from app.core.logging import get_logger
from app.core.security import hash_token, new_api_key
from app.exceptions import EntityNotFound
from app.models.organizations import ApiKey
from app.models.users import User, UserRole
from app.repositories.api_key import ApiKeyRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)

SERVICE_EMAIL_DOMAIN = "service.call-insight.local"


class ApiKeyService:
    """API keys for external systems, each backed by a service user."""

    def __init__(
        self,
        session: AsyncSession,
        repo: ApiKeyRepository,
        users: UserRepository,
    ) -> None:
        self.session = session
        self.repo = repo
        self.users = users

    async def create(self, actor: User, name: str) -> tuple[ApiKey, str]:
        secret, prefix, key_hash = new_api_key(API_KEY_PREFIX_LEN)

        service_user = await self.users.create(
            User(
                email=f"{prefix}@{SERVICE_EMAIL_DOMAIN}",
                hashed_password="",
                first_name="Ключ",
                last_name=name,
                role=UserRole.ADMIN,
                organization_id=actor.organization_id,
                email_verified_at=datetime.now(UTC),
            )
        )

        key = await self.repo.create(
            ApiKey(
                organization_id=actor.organization_id,
                user_id=service_user.id,
                name=name,
                prefix=prefix,
                key_hash=key_hash,
            )
        )
        await self.session.commit()
        logger.info(
            "api key created | by=%s org=%s prefix=%s",
            actor.id,
            actor.organization_id,
            prefix,
        )
        return key, secret

    async def list_keys(self, actor: User) -> Sequence[ApiKey]:
        return await self.repo.list_for_organization(actor.organization_id)

    async def revoke(self, actor: User, key_id: int) -> ApiKey:
        key = await self.repo.get_for_organization(key_id, actor.organization_id)
        if key is None:
            raise EntityNotFound(entity="ApiKey", id=key_id)

        if key.revoked_at is None:
            key.revoked_at = datetime.now(UTC)
            service_user = await self.users.get(key.user_id)
            if service_user is not None:
                service_user.is_active = False
            await self.session.commit()
            logger.info("api key revoked | by=%s prefix=%s", actor.id, key.prefix)

        return key

    async def authenticate(self, secret: str) -> User | None:
        key = await self.repo.get_active_by_hash(hash_token(secret))
        if key is None or not key.user.is_active:
            return None

        await self._touch(key)
        return key.user

    async def _touch(self, key: ApiKey) -> None:
        """Update last_used_at at most once per configured interval."""
        now = datetime.now(UTC)
        threshold = now - timedelta(seconds=settings.api_key_touch_seconds)
        if key.last_used_at is not None and key.last_used_at > threshold:
            return

        key.last_used_at = now
        await self.session.commit()
