import asyncio
from datetime import UTC, datetime

from app.core.db import async_session
from app.core.security import hash_password
from app.fixtures.checklist import CHECKLIST
from app.fixtures.users import SEED_PASSWORD, USERS
from app.models.checklist import ChecklistItem
from app.models.users import User, UserRole
from app.repositories.checklist import ChecklistRepository
from app.repositories.user import UserRepository


async def seed_checklist() -> None:
    async with async_session() as session:
        repo = ChecklistRepository(session)

        for row in CHECKLIST:
            item = await repo.get_by_code(row["code"])
            if item is None:
                session.add(ChecklistItem(**row))
                continue

            item.title = row["title"]
            item.description = row["description"]
            item.weight = row["weight"]
            item.is_required = row["is_required"]

        await session.commit()


async def seed_users() -> None:
    async with async_session() as session:
        repo = UserRepository(session)

        for row in USERS:
            user = await repo.get_by_email(row["email"])
            if user is not None:
                if user.email_verified_at is None:
                    user.email_verified_at = datetime.now(UTC)
                if not user.hashed_password.startswith("$2"):
                    user.hashed_password = hash_password(SEED_PASSWORD)
                continue

            session.add(
                User(
                    email=row["email"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    role=UserRole(row["role"]),
                    hashed_password=hash_password(SEED_PASSWORD),
                    email_verified_at=datetime.now(UTC),
                )
            )

        await session.commit()


async def seed_all() -> None:
    await seed_users()
    await seed_checklist()


if __name__ == "__main__":
    asyncio.run(seed_all())
