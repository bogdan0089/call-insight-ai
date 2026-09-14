from sqlalchemy import select

from app.models.organizations import Organization
from app.repositories.base_repository import SqlalchemyAsyncRepository


class OrganizationRepository(SqlalchemyAsyncRepository[Organization]):
    model = Organization

    async def get_by_slug(self, slug: str) -> Organization | None:
        return await self.get_by(slug=slug)

    async def taken_slugs(self, base: str) -> set[str]:
        stmt = select(Organization.slug).where(Organization.slug.like(f"{base}%"))
        result = await self.session.execute(stmt)
        return set(result.scalars().all())
