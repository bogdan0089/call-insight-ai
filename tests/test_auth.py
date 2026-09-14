import logging
import re
import uuid
from collections.abc import Iterator

import httpx
import pytest

MAIL_LOGGER = "app.integrations.mail.client"


@pytest.fixture
def mailbox() -> Iterator[list[str]]:
    messages: list[str] = []

    class Catcher(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    logger = logging.getLogger(MAIL_LOGGER)
    handler = Catcher()
    previous = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield messages
    logger.removeHandler(handler)
    logger.setLevel(previous)


def new_email() -> str:
    return f"user{uuid.uuid4().hex[:10]}@example.com"


def token_from(messages: list[str]) -> str:
    match = re.search(r"token=(\S+)", "\n".join(messages))
    assert match is not None, "verification mail was not sent"
    return match.group(1)


async def register(
    client: httpx.AsyncClient,
    email: str,
    password: str = "secret123",
    organization_name: str = "Тестова компанія",
):
    return await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Тест",
            "last_name": "Користувач",
            "organization_name": organization_name,
        },
    )


@pytest.mark.asyncio
async def test_registration_sends_a_verification_link(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    response = await register(client, new_email())

    assert response.status_code == 202
    assert token_from(mailbox)


@pytest.mark.asyncio
async def test_login_is_refused_until_the_email_is_verified(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    email = new_email()
    await register(client, email)

    before = await client.post(
        "/auth/login", json={"email": email, "password": "secret123"}
    )
    assert before.status_code == 403

    await client.post("/auth/verify", json={"token": token_from(mailbox)})

    after = await client.post(
        "/auth/login", json={"email": email, "password": "secret123"}
    )
    assert after.status_code == 200
    assert after.json()["user"]["is_verified"] is True


@pytest.mark.asyncio
async def test_verification_token_works_once(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    await register(client, new_email())
    token = token_from(mailbox)

    assert (await client.post("/auth/verify", json={"token": token})).status_code == 200
    assert (await client.post("/auth/verify", json={"token": token})).status_code == 400


@pytest.mark.asyncio
async def test_registering_a_taken_email_reveals_nothing(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    email = new_email()
    first = await register(client, email)
    second = await register(client, email)

    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_wrong_password_is_not_distinguishable_from_unknown_email(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    email = new_email()
    await register(client, email)
    await client.post("/auth/verify", json={"token": token_from(mailbox)})

    wrong = await client.post(
        "/auth/login", json={"email": email, "password": "wrongpass1"}
    )
    unknown = await client.post(
        "/auth/login", json={"email": new_email(), "password": "secret123"}
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


@pytest.mark.asyncio
async def test_me_returns_the_signed_in_user(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    email = new_email()
    await register(client, email)
    await client.post("/auth/verify", json={"token": token_from(mailbox)})
    token = (
        await client.post("/auth/login", json={"email": email, "password": "secret123"})
    ).json()["access_token"]

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == email
    assert body["user"]["role"] == "owner"
    assert body["organization"]["name"] == "Тестова компанія"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Basic whatever"}],
)
async def test_me_requires_a_valid_token(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> None:
    assert (await client.get("/auth/me", headers=headers)).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password",
    ["short1", "nodigitshere", "12345678"],
)
async def test_weak_passwords_are_rejected(
    client: httpx.AsyncClient,
    password: str,
) -> None:
    assert (await register(client, new_email(), password)).status_code == 422


@pytest.mark.asyncio
async def test_malformed_email_is_rejected(client: httpx.AsyncClient) -> None:
    assert (await register(client, "not-an-email")).status_code == 422


@pytest.mark.asyncio
async def test_errors_carry_a_stable_code(
    client: httpx.AsyncClient,
    mailbox: list[str],
) -> None:
    email = new_email()
    await register(client, email)

    unverified = await client.post(
        "/auth/login", json={"email": email, "password": "secret123"}
    )
    wrong = await client.post(
        "/auth/login", json={"email": new_email(), "password": "secret123"}
    )

    assert unverified.json()["code"] == "EmailNotVerified"
    assert wrong.json()["code"] == "InvalidCredentials"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/auth/register", "/auth/login", "/auth/resend"])
async def test_overlong_email_is_rejected_before_the_database(
    client: httpx.AsyncClient,
    path: str,
) -> None:
    email = f"{'a' * 60}@example.com"
    payload = {
        "email": email,
        "password": "secret123",
        "first_name": "Тест",
        "last_name": "Користувач",
        "organization_name": "Тестова компанія",
    }

    assert (await client.post(path, json=payload)).status_code == 422
