"""Sliding-window rate limiting backed by Redis."""

import math
import time
from dataclasses import dataclass
from functools import cache

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.exceptions import RateLimitUnavailable

logger = get_logger(__name__)

KEY_PREFIX = "rl"

SLIDING_WINDOW = """
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local current_start = now - (now % window)
local current_key = KEYS[1] .. ':' .. current_start
local previous_key = KEYS[1] .. ':' .. (current_start - window)

local previous = tonumber(redis.call('GET', previous_key) or '0')
local current = tonumber(redis.call('GET', current_key) or '0')
local weight = 1 - (now - current_start) / window
local estimated = previous * weight + current

if estimated >= limit then
  return {0, math.floor(estimated), window - (now - current_start)}
end

current = redis.call('INCR', current_key)
redis.call('PEXPIRE', current_key, window * 2)
return {1, math.floor(previous * weight + current), 0}
"""


@dataclass(frozen=True, slots=True)
class Rule:
    limit: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


@cache
def rule_for(name: str) -> Rule:
    raw = settings.rate_limits.get(name)
    if raw is None:
        raise KeyError(f"rate limit rule '{name}' is not configured")

    limit, _, window = raw.partition("/")
    rule = Rule(limit=int(limit), window_seconds=int(window))
    if rule.limit <= 0 or rule.window_seconds <= 0:
        raise ValueError(f"rate limit rule '{name}' must be positive: {raw}")
    return rule


async def hit(rule_name: str, identity: str) -> Decision:
    """Count an attempt and decide whether to allow it."""
    rule = rule_for(rule_name)

    if not settings.rate_limit_enabled:
        return Decision(True, rule.limit, rule.limit, 0)

    key = f"{KEY_PREFIX}:{rule_name}:{identity}"
    window_ms = rule.window_seconds * 1000

    try:
        allowed, count, retry_ms = await get_redis().eval(
            SLIDING_WINDOW,
            1,
            key,
            int(time.time() * 1000),
            window_ms,
            rule.limit,
        )
    except RedisError as exc:
        if not settings.rate_limit_fail_open:
            raise RateLimitUnavailable from exc
        logger.error(
            "rate limit unavailable, letting request through | rule=%s | %s",
            rule_name,
            exc,
        )
        return Decision(True, rule.limit, rule.limit, 0)

    return Decision(
        allowed=bool(allowed),
        limit=rule.limit,
        remaining=max(rule.limit - int(count), 0),
        retry_after=math.ceil(int(retry_ms) / 1000),
    )
