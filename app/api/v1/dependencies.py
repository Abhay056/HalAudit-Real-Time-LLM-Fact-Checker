"""
HalAudit API v1 Dependencies
Shared dependencies for route handlers.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.config import get_settings, Settings
from app.db.redis_client import get_redis

logger = logging.getLogger(__name__)


def get_app_settings() -> Settings:
    """Dependency to inject application settings."""
    return get_settings()


async def check_redis_available():
    """Dependency to check if Redis is available for async operations."""
    redis = await get_redis()
    if redis is None:
        raise HTTPException(
            status_code=503,
            detail="Async processing unavailable. Redis is not connected."
        )
    return redis


async def get_optional_redis():
    """Dependency that returns Redis client or None."""
    return await get_redis()
