"""Shared FastAPI dependency-injection utilities.

Business modules should import ``get_db`` / ``get_redis`` from here
rather than reaching into :mod:`app.database.session` or
:mod:`app.core.redis` directly. This indirection keeps a single seam for
swapping implementations (e.g. during tests) and keeps module code
decoupled from infrastructure details.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.session import get_session
from app.core.redis import get_redis_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped ``AsyncSession``."""
    async for session in get_session():
        yield session


def get_redis() -> Redis:
    """FastAPI dependency returning the shared async Redis client."""
    return get_redis_client()


def get_app_settings() -> Settings:
    """FastAPI dependency returning the cached application settings."""
    return get_settings()


# Reusable typed annotations for concise route/service signatures, e.g.:
#
#   async def some_endpoint(db: DBSession, redis: RedisClient) -> ...:
#       ...
DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
