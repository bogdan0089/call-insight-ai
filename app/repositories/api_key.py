from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.organizations import ApiKey
from app.repositories.base_repository import SqlalchemyAsyncRepository


class ApiKeyRepository(SqlalchemyAsyncRepository[ApiKey]):
    model = ApiKey

    async def get_active_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = (
            select(ApiKey)
            .where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
            .options(selectinload(ApiKey.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_organization(self, organization_id: int) -> Sequence[ApiKey]:
        stmt = (
            select(ApiKey)
            .where(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.revoked_at.is_not(None), ApiKey.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_for_organization(
        self,
        key_id: int,
        organization_id: int,
    ) -> ApiKey | None:
        stmt = select(ApiKey).where(
            ApiKey.id == key_id, ApiKey.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
