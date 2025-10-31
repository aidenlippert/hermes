"""
Rate Limiting Middleware

Redis-based rate limiting with tiered limits based on subscription tier.
"""

import logging
import time
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client

        # Rate limits by subscription tier (requests per minute)
        self.tier_limits = {
            "free": 10,
            "pro": 100,
            "enterprise": 1000,
            "agent": 500,  # For agent-to-agent calls
        }

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (user_id, ip, agent_id)
            limit: Max requests per window
            window: Time window in seconds (default 60)

        Returns:
            (allowed, info) where info contains limit details
        """
        if not self.redis:
            # No Redis available, allow all requests
            logger.warning("Redis not available, rate limiting disabled")
            return True, {"limit": limit, "remaining": limit, "reset": 0}

        try:
            current_time = int(time.time())
            window_key = f"ratelimit:{key}:{current_time // window}"

            # Get current count
            count = await self.redis.get(window_key)
            current_count = int(count) if count else 0

            if current_count >= limit:
                # Rate limit exceeded
                reset_time = ((current_time // window) + 1) * window
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "retry_after": reset_time - current_time
                }

            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, window * 2)  # Keep for 2 windows
            await pipe.execute()

            reset_time = ((current_time // window) + 1) * window
            return True, {
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset": reset_time
            }

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request
            return True, {"limit": limit, "remaining": limit, "reset": 0}

    def get_limit_for_tier(self, tier: str) -> int:
        """Get rate limit for subscription tier"""
        return self.tier_limits.get(tier, self.tier_limits["free"])


def create_rate_limit_middleware(redis_client: Optional[redis.Redis] = None):
    """Create rate limiting middleware factory"""

    limiter = RateLimiter(redis_client)

    async def rate_limit_middleware(request: Request, call_next: Callable):
        """
        Rate limit middleware

        Applies different limits based on:
        - Authenticated user's subscription tier
        - IP address for unauthenticated requests
        - Agent API key for agent-to-agent calls
        """

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        # Determine rate limit key and tier
        user = getattr(request.state, "user", None)
        agent = getattr(request.state, "agent", None)

        if agent:
            # Agent-to-agent call
            key = f"agent:{agent.id}"
            tier = "agent"
        elif user:
            # Authenticated user
            key = f"user:{user.id}"
            tier = user.subscription_tier if hasattr(user, 'subscription_tier') else "free"
        else:
            # Unauthenticated - use IP
            client_ip = request.client.host if request.client else "unknown"
            key = f"ip:{client_ip}"
            tier = "free"

        limit = limiter.get_limit_for_tier(tier)
        allowed, info = await limiter.check_rate_limit(key, limit)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "limit": info["limit"],
                    "remaining": info["remaining"],
                    "reset": info["reset"],
                    "retry_after": info["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"])
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response

    return rate_limit_middleware


# Decorator for endpoint-specific rate limiting
def rate_limit(requests_per_minute: int):
    """
    Decorator for custom endpoint rate limiting

    Usage:
        @router.post("/expensive-operation")
        @rate_limit(5)  # Max 5 requests per minute
        async def expensive_operation():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need request context
            # For now, just pass through
            # TODO: Implement decorator-based rate limiting
            return await func(*args, **kwargs)
        return wrapper
    return decorator
