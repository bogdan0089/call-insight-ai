import httpx
import pytest

from app.models.users import User, UserRole
from tests.conftest import auth_header, make_org_user

AUDIO = {"file": ("call.mp3", b"\xff\xfb\x90fake", "audio/mpeg")}


async def issue_key(client: httpx.AsyncClient, owner: User, name: str = "CRM") -> str:
    response = await client.post(
        "/api-keys", headers=auth_header(owner), json={"name": name}
    )
    assert response.status_code == 201
    return response.json()["secret"]


@pytest.mark.asyncio
async def test_the_secret_is_returned_once_and_never_stored(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    created = await client.post(
        "/api-keys", headers=auth_header(owner), json={"name": "CRM"}
    )
    listed = await client.get("/api-keys", headers=auth_header(owner))

    secret = created.json()["secret"]
    assert secret.startswith("ci_")
    assert all("secret" not in key for key in listed.json())
    assert listed.json()[0]["prefix"] in secret


@pytest.mark.asyncio
async def test_a_key_can_read_and_write_calls(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    secret = await issue_key(client, owner)
    headers = {"X-API-Key": secret}

    uploaded = await client.post("/calls", files=AUDIO, headers=headers)
    listed = await client.get("/calls", headers=headers)

    assert uploaded.status_code == 202
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


@pytest.mark.asyncio
async def test_a_key_sees_only_its_own_company(client: httpx.AsyncClient) -> None:
    ours = await make_org_user(UserRole.OWNER)
    theirs = await make_org_user(UserRole.OWNER)
    secret = await issue_key(client, ours)

    await client.post("/calls", files=AUDIO, headers={"X-API-Key": secret})
    alien = await client.get("/calls", headers=auth_header(theirs))

    assert alien.json()["total"] == 0


@pytest.mark.asyncio
async def test_a_revoked_key_stops_working(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    created = await client.post(
        "/api-keys", headers=auth_header(owner), json={"name": "CRM"}
    )
    headers = {"X-API-Key": created.json()["secret"]}
    key_id = created.json()["key"]["id"]

    before = await client.get("/calls", headers=headers)
    await client.delete(f"/api-keys/{key_id}", headers=auth_header(owner))
    after = await client.get("/calls", headers=headers)

    assert before.status_code == 200
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_a_made_up_key_is_refused(client: httpx.AsyncClient) -> None:
    response = await client.get("/calls", headers={"X-API-Key": "ci_dead_beef"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_keys_of_another_company_are_invisible(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    stranger = await make_org_user(UserRole.OWNER)
    await issue_key(client, owner)

    listing = await client.get("/api-keys", headers=auth_header(stranger))

    assert listing.json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR])
async def test_only_the_owner_manages_keys(
    client: httpx.AsyncClient,
    role: UserRole,
) -> None:
    person = await make_org_user(role)

    response = await client.get("/api-keys", headers=auth_header(person))

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_service_users_stay_out_of_the_team(
    client: httpx.AsyncClient,
    owner: User,
) -> None:
    secret = await issue_key(client, owner)
    me = await client.get("/auth/me", headers={"X-API-Key": secret})
    service_user_id = me.json()["user"]["id"]

    listing = await client.get("/people", headers=auth_header(owner))
    update = await client.patch(
        f"/people/{service_user_id}",
        headers=auth_header(owner),
        json={"is_active": False},
    )

    assert service_user_id not in [person["id"] for person in listing.json()["items"]]
    assert update.status_code == 404
