"""
HalAudit Rate Limiting Middleware
Redis-backed sliding window rate limiter with informative headers.
"""

import time
import logging
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.db.redis_client import get_redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed sliding window rate limiter.
    Falls back to allowing all requests if Redis is unavailable.
    """

    # Exempt paths from rate limiting
    EXEMPT_PATHS = {"/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json", "/"}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths and static files
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith("/dashboard") or path.startswith("/static"):
            return await call_next(request)

        # Only rate limit API endpoints
        if not path.startswith("/api/"):
            return await call_next(request)

        settings = get_settings()
        limit = settings.rate_limit_per_minute
        window = 60  # seconds

        # Get client identifier (IP-based for now)
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"ratelimit:{client_ip}:{path}"

        redis = await get_redis()

        if redis is None:
            # Redis unavailable — fail open (allow request)
            response = await call_next(request)
            return response

        try:
            now = time.time()
            window_start = now - window

            pipe = redis.pipeline()
            # Remove old entries outside the window
            pipe.zremrangebyscore(rate_key, 0, window_start)
            # Add current request
            pipe.zadd(rate_key, {str(now): now})
            # Count requests in window
            pipe.zcard(rate_key)
            # Set TTL on the key
            pipe.expire(rate_key, window + 1)
            results = await pipe.execute()

            request_count = results[2]
            remaining = max(0, limit - request_count)

            if request_count > limit:
                # Rate limit exceeded
                reset_time = int(window_start + window)
                retry_after = int(window - (now - window_start))

                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {path}: "
                    f"{request_count}/{limit}"
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Maximum {limit} requests per minute. Try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(retry_after),
                    }
                )

            # Process the request
            response = await call_next(request)

            # Add rate limit headers to successful responses
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(now + window))

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open on error
            return await call_next(request)
