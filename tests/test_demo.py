import uuid
from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import settings
from app.core.db import async_session
from app.models.users import User, UserRole
from tests.conftest import make_org_user


@pytest.fixture
async def demo_email(monkeypatch: pytest.MonkeyPatch) -> str:
    owner = await make_org_user(UserRole.OWNER)
    email = f"demo{uuid.uuid4().hex[:8]}@example.com"
    async with async_session() as session:
        session.add(
            User(
                email=email,
                hashed_password="",
                first_name="Demo",
                last_name="Viewer",
                role=UserRole.OWNER,
                organization_id=owner.organization_id,
                email_verified_at=datetime.now(UTC),
            )
        )
        await session.commit()
    monkeypatch.setattr(settings, "demo_email", email)
    monkeypatch.setattr(settings, "demo_enabled", True)
    return email


async def demo_headers(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.post("/auth/demo")
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_demo_is_hidden_when_disabled(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "demo_enabled", False)

    assert (await client.post("/auth/demo")).status_code == 404


@pytest.mark.asyncio
async def test_demo_login_needs_a_configured_account(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "demo_enabled", True)
    monkeypatch.setattr(settings, "demo_email", f"missing{uuid.uuid4().hex}@example.com")

    assert (await client.post("/auth/demo")).status_code == 404


@pytest.mark.asyncio
async def test_demo_can_read(client: httpx.AsyncClient, demo_email: str) -> None:
    headers = await demo_headers(client)

    profile = await client.get("/auth/me", headers=headers)

    assert profile.status_code == 200
    assert profile.json()["is_demo"] is True
    assert (await client.get("/calls", headers=headers)).status_code == 200
    assert (await client.get("/stats/daily", headers=headers)).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api-keys", {"name": "spam"}),
        (
            "post",
            "/people",
            {"email": "victim@example.com", "first_name": "A", "last_name": "B"},
        ),
        ("patch", "/calls/1/scores/1", {"is_verified": True}),
    ],
)
async def test_demo_cannot_change_anything(
    client: httpx.AsyncClient,
    demo_email: str,
    method: str,
    path: str,
    body: dict,
) -> None:
    headers = await demo_headers(client)

    response = await getattr(client, method)(path, json=body, headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "PermissionDenied"


@pytest.mark.asyncio
async def test_demo_account_has_no_password_login(
    client: httpx.AsyncClient,
    demo_email: str,
) -> None:
    response = await client.post(
        "/auth/login", json={"email": demo_email, "password": "anything1"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_regular_users_are_not_restricted(
    client: httpx.AsyncClient,
    demo_email: str,
) -> None:
    from tests.conftest import auth_header

    owner = await make_org_user(UserRole.OWNER)
    response = await client.post(
        "/api-keys", headers=auth_header(owner), json={"name": "CRM"}
    )

    assert response.status_code == 201
