from collections.abc import Sequence
from typing import Any

from sqlalchemy import insert, select

from app.models.checklist import ChecklistItem
from app.repositories.base_repository import SqlalchemyAsyncRepository


class ChecklistRepository(SqlalchemyAsyncRepository[ChecklistItem]):
    model = ChecklistItem

    async def get_active(self, organization_id: int | None) -> Sequence[ChecklistItem]:
        stmt = select(ChecklistItem).where(
            ChecklistItem.is_active.is_(True),
            ChecklistItem.organization_id == organization_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_code(
        self,
        code: str,
        organization_id: int | None,
    ) -> ChecklistItem | None:
        return await self.get_by(code=code, organization_id=organization_id)

    async def add_many(
        self,
        organization_id: int,
        rows: list[dict[str, Any]],
    ) -> None:
        """Insert checklist items in one statement."""
        if not rows:
            return

        await self.session.execute(
            insert(ChecklistItem),
            [{"organization_id": organization_id, **row} for row in rows],
        )
