from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.config import settings
from app.core.rate_limit import hit
from app.exceptions import TooManyRequests

UNKNOWN_CLIENT = "unknown"


def client_ip(request: Request) -> str:
    """Client IP; X-Forwarded-For is trusted only behind a known proxy."""
    if settings.trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client else UNKNOWN_CLIENT


async def enforce(rule: str, identity: str) -> None:
    decision = await hit(rule, identity)
    if not decision.allowed:
        raise TooManyRequests(retry_after=decision.retry_after, limit=decision.limit)


def limit_by_ip(rule: str) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        await enforce(rule, client_ip(request))

    return dependency
