import uuid

import httpx
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core import rate_limit
from app.core.config import settings
from app.models.users import User
from tests.conftest import auth_header


def unique(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_requests_within_the_limit_pass(rate_limits) -> None:
    rule = unique("t")
    rate_limits(**{rule: "3/60"})

    decisions = [await rate_limit.hit(rule, "client") for _ in range(3)]

    assert all(decision.allowed for decision in decisions)
    assert [decision.remaining for decision in decisions] == [2, 1, 0]


@pytest.mark.asyncio
async def test_the_request_over_the_limit_is_refused(rate_limits) -> None:
    rule = unique("t")
    rate_limits(**{rule: "2/60"})

    for _ in range(2):
        await rate_limit.hit(rule, "client")
    refused = await rate_limit.hit(rule, "client")

    assert refused.allowed is False
    assert 0 < refused.retry_after <= 60


@pytest.mark.asyncio
async def test_different_identities_have_separate_budgets(rate_limits) -> None:
    rule = unique("t")
    rate_limits(**{rule: "1/60"})

    first = await rate_limit.hit(rule, "alice")
    second = await rate_limit.hit(rule, "bob")

    assert first.allowed and second.allowed


@pytest.mark.asyncio
async def test_login_is_throttled_per_email(
    client: httpx.AsyncClient,
    rate_limits,
) -> None:
    rate_limits(login_email="3/300", login_ip="1000/300", ip="1000/60")
    email = f"victim{uuid.uuid4().hex[:8]}@example.com"
    attempt = {"email": email, "password": "wrong-pass1"}

    statuses = [
        (await client.post("/auth/login", json=attempt)).status_code for _ in range(4)
    ]

    assert statuses == [401, 401, 401, 429]


@pytest.mark.asyncio
async def test_throttled_response_says_when_to_retry(
    client: httpx.AsyncClient,
    rate_limits,
) -> None:
    rate_limits(login_email="1/300", login_ip="1000/300", ip="1000/60")
    attempt = {"email": f"v{uuid.uuid4().hex[:8]}@example.com", "password": "wrong-pass1"}

    await client.post("/auth/login", json=attempt)
    refused = await client.post("/auth/login", json=attempt)

    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 0
    assert refused.headers["X-RateLimit-Limit"] == "1"


@pytest.mark.asyncio
async def test_authenticated_traffic_has_its_own_budget(
    client: httpx.AsyncClient,
    owner: User,
    rate_limits,
) -> None:
    rate_limits(principal="2/60", ip="1000/60")
    headers = auth_header(owner)

    statuses = [(await client.get("/auth/me", headers=headers)).status_code for _ in range(3)]

    assert statuses == [200, 200, 429]


@pytest.mark.asyncio
async def test_forwarded_for_is_ignored_unless_trusted(
    client: httpx.AsyncClient,
    rate_limits,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rate_limits(login_ip="1/300", login_email="1000/300", ip="1000/60")
    monkeypatch.setattr(settings, "trust_forwarded_for", False)

    def attempt(spoofed: str) -> dict:
        return {
            "json": {"email": f"x{uuid.uuid4().hex[:8]}@example.com", "password": "wrong1"},
            "headers": {"X-Forwarded-For": spoofed},
        }

    await client.post("/auth/login", **attempt("1.1.1.1"))
    spoofed = await client.post("/auth/login", **attempt("2.2.2.2"))

    assert spoofed.status_code == 429


@pytest.mark.asyncio
async def test_redis_outage_lets_traffic_through_when_fail_open(
    rate_limits,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = unique("t")
    rate_limits(**{rule: "1/60"})
    monkeypatch.setattr(settings, "rate_limit_fail_open", True)

    class BrokenRedis:
        async def eval(self, *args, **kwargs):
            raise RedisConnectionError("down")

    monkeypatch.setattr(rate_limit, "get_redis", lambda: BrokenRedis())

    decision = await rate_limit.hit(rule, "client")

    assert decision.allowed is True


@pytest.mark.asyncio
async def test_forwarded_for_splits_budgets_behind_a_trusted_proxy(
    client: httpx.AsyncClient,
    rate_limits,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rate_limits(login_ip="1/300", login_email="1000/300", ip="1000/60")
    monkeypatch.setattr(settings, "trust_forwarded_for", True)
    tag = uuid.uuid4().hex[:6]

    def attempt(address: str) -> dict:
        return {
            "json": {"email": f"y{uuid.uuid4().hex[:8]}@example.com", "password": "wrong1"},
            "headers": {"X-Forwarded-For": address},
        }

    first = await client.post("/auth/login", **attempt(f"10.0.0.1-{tag}"))
    second = await client.post("/auth/login", **attempt(f"10.0.0.2-{tag}"))

    assert first.status_code == 401
    assert second.status_code == 401


@pytest.mark.asyncio
async def test_browser_can_read_retry_after_across_origins(
    client: httpx.AsyncClient,
    rate_limits,
) -> None:
    rate_limits(login_email="1/300", login_ip="1000/300", ip="1000/60")
    attempt = {"email": f"c{uuid.uuid4().hex[:8]}@example.com", "password": "wrong-pass1"}
    origin = {"Origin": "http://localhost:3100"}

    await client.post("/auth/login", json=attempt, headers=origin)
    refused = await client.post("/auth/login", json=attempt, headers=origin)

    exposed = refused.headers.get("access-control-expose-headers", "").lower()
    assert refused.status_code == 429
    assert "retry-after" in exposed
