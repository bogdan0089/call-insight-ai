import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx
import pytest

from app.core.db import async_session, engine
from app.core.security import create_access_token, hash_password
from app.core.slug import slugify, unique_slug
from app.main import app
from app.models.organizations import Organization
from app.models.users import User, UserRole
from app.workers import tasks


@pytest.fixture(autouse=True)
async def dispose_engine() -> AsyncGenerator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def no_celery(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    published: list[int] = []
    monkeypatch.setattr(tasks.process_call, "delay", published.append)
    return published


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def make_org_user(
    role: UserRole,
    manager_id: int | None = None,
    organization_id: int | None = None,
) -> User:
    """Create a verified user in a new or given organization."""
    suffix = uuid.uuid4().hex[:8]
    async with async_session() as session:
        if organization_id is None:
            organization = Organization(
                name=f"Company {suffix}",
                slug=unique_slug(slugify(f"company {suffix}", 64), set(), 64),
            )
            session.add(organization)
            await session.flush()
            organization_id = organization.id

        user = User(
            email=f"{role.value}{suffix}@example.com",
            hashed_password=hash_password("secret123"),
            first_name="Тест",
            last_name=role.value,
            role=role,
            organization_id=organization_id,
            manager_id=manager_id,
            email_verified_at=datetime.now(UTC),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(user_id=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def owner() -> User:
    return await make_org_user(UserRole.OWNER)


@pytest.fixture
async def auth_client(owner: User) -> AsyncGenerator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=auth_header(owner),
    ) as client:
        yield client

