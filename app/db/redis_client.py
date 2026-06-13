"""
HalAudit Redis Client
Async Redis connection manager with health checks and graceful shutdown.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """
    Get the async Redis client. Returns None if Redis is unavailable.
    """
    global _redis_pool

    if _redis_pool is not None:
        try:
            await _redis_pool.ping()
            return _redis_pool
        except Exception:
            logger.warning("Redis connection lost, attempting reconnect...")
            _redis_pool = None

    try:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
        )
        await _redis_pool.ping()
        logger.info(f"Redis connected: {settings.redis_url}")
        return _redis_pool
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}. Running without async queue support.")
        _redis_pool = None
        return None


async def close_redis():
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("Redis connection closed")


async def redis_health_check() -> dict:
    """Check Redis health status."""
    try:
        r = await get_redis()
        if r is None:
            return {"status": "unavailable", "message": "Redis not connected"}

        info = await r.info("server")
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
        }
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
