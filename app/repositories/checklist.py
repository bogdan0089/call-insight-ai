from collections.abc import Sequence

from sqlalchemy import select

from app.models.checklist import ChecklistItem
from app.repositories.base_repository import SqlalchemyAsyncRepository


class ChecklistRepository(SqlalchemyAsyncRepository[ChecklistItem]):
    model = ChecklistItem

    async def get_active(self) -> Sequence[ChecklistItem]:
        stmt = select(ChecklistItem).where(ChecklistItem.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_code(self, code: str) -> ChecklistItem | None:
        return await self.get_by(code=code)
