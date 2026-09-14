import logging
import re
import uuid

import httpx
import pytest

from app.models.users import User, UserRole
from tests.conftest import auth_header, make_org_user

MAIL_LOGGER = "app.integrations.mail.client"


def new_person(role: str = "operator") -> dict[str, str]:
    return {
        "email": f"invited{uuid.uuid4().hex[:10]}@example.com",
        "first_name": "Запрошений",
        "last_name": "Працівник",
        "role": role,
    }


@pytest.mark.asyncio
async def test_owner_invites_a_person_without_a_password(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    response = await client.post("/people", headers=auth_header(owner), json=new_person())

    assert response.status_code == 201
    body = response.json()
    assert body["is_verified"] is False
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_invited_person_cannot_log_in_before_accepting(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    payload = new_person()
    await client.post("/people", headers=auth_header(owner), json=payload)

    response = await client.post(
        "/auth/login", json={"email": payload["email"], "password": "secret123"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_manager_can_invite_only_operators_under_themselves(
    client: httpx.AsyncClient,
) -> None:
    manager = await make_org_user(UserRole.MANAGER)

    operator = await client.post(
        "/people", headers=auth_header(manager), json=new_person()
    )
    admin = await client.post(
        "/people", headers=auth_header(manager), json=new_person("admin")
    )

    assert operator.status_code == 201
    assert operator.json()["manager_id"] == manager.id
    assert admin.status_code == 403


@pytest.mark.asyncio
async def test_operator_cannot_reach_people(client: httpx.AsyncClient) -> None:
    operator = await make_org_user(UserRole.OPERATOR)

    assert (await client.get("/people", headers=auth_header(operator))).status_code == 403


@pytest.mark.asyncio
async def test_people_list_never_crosses_companies(client: httpx.AsyncClient) -> None:
    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)
    await client.post("/people", headers=auth_header(ours), json=new_person())

    listing = await client.get("/people", headers=auth_header(theirs))

    assert listing.status_code == 200
    assert [person["id"] for person in listing.json()["items"]] == [theirs.id]


@pytest.mark.asyncio
async def test_nobody_can_change_their_own_access(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    response = await client.patch(
        f"/people/{owner.id}", headers=auth_header(owner), json={"is_active": False}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_a_person_from_another_company_is_not_found(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    stranger = await make_org_user(UserRole.OPERATOR)

    response = await client.patch(
        f"/people/{stranger.id}", headers=auth_header(owner), json={"is_active": False}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_email_is_refused(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    payload = new_person()
    first = await client.post("/people", headers=auth_header(owner), json=payload)
    second = await client.post("/people", headers=auth_header(owner), json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_deactivated_person_loses_access(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    victim = await make_org_user(
        UserRole.MANAGER, organization_id=owner.organization_id
    )

    before = await client.get("/people", headers=auth_header(victim))
    await client.patch(
        f"/people/{victim.id}", headers=auth_header(owner), json={"is_active": False}
    )
    after = await client.get("/people", headers=auth_header(victim))

    assert before.status_code == 200
    assert after.status_code == 403


@pytest.mark.asyncio
async def test_invited_person_sets_a_password_and_logs_in(
    client: httpx.AsyncClient,
    owner: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=MAIL_LOGGER)
    payload = new_person()
    await client.post("/people", headers=auth_header(owner), json=payload)

    match = re.search(r"invite\?token=(\S+)", caplog.text)
    assert match is not None, "invitation mail was not sent"

    accepted = await client.post(
        "/auth/accept-invite", json={"token": match.group(1), "password": "newpass123"}
    )
    login = await client.post(
        "/auth/login", json={"email": payload["email"], "password": "newpass123"}
    )
    reused = await client.post(
        "/auth/accept-invite", json={"token": match.group(1), "password": "other1234"}
    )

    assert accepted.status_code == 200
    assert accepted.json()["is_verified"] is True
    assert login.status_code == 200
    assert reused.status_code == 400


@pytest.mark.asyncio
async def test_overlong_invite_email_is_rejected(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    payload = {**new_person(), "email": f"{'a' * 60}@example.com"}

    response = await client.post("/people", headers=auth_header(owner), json=payload)

    assert response.status_code == 422
