"""
Simple Redis-based rate limiting utilities.

Supports sliding window via fixed window with TTL for MVP.
"""
from __future__ import annotations
import asyncio
from typing import Optional
from datetime import datetime, timezone

from backend.database.connection import get_redis


async def check_and_increment(key: str, limit: int, window_seconds: int = 60) -> bool:
    """Return True if within limit after increment, else False.

    Uses Redis INCR with TTL for a fixed window counter.
    """
    redis = await get_redis()
    if not redis:
        # No Redis -> allow by default
        return True
    now_key = f"{key}:{int(datetime.now(timezone.utc).timestamp() // window_seconds)}"
    # Increment
    count = await redis.incr(now_key)
    if count == 1:
        await redis.expire(now_key, window_seconds)
    return count <= max(1, limit)


def rl_key_for_api_key(api_key_id: str) -> str:
    return f"rl:api:{api_key_id}"


def rl_key_for_org(org_id: str) -> str:
    return f"rl:org:{org_id}"
