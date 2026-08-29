import asyncio

from app.core.db import async_session
from app.fixtures.checklist import CHECKLIST
from app.models.checklist import ChecklistItem
from app.repositories.checklist import ChecklistRepository


async def seed_checklist() -> None:
    async with async_session() as session:
        repo = ChecklistRepository(session)

        for row in CHECKLIST:
            item = await repo.get_by_code(row["code"])
            if item is None:
                item = ChecklistItem(**row)
                session.add(item)
                continue

            item.title = row["title"]
            item.description = row["description"]
            item.weight = row["weight"]
            item.is_required = row["is_required"]

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_checklist())
