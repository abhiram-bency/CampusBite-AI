"""Redis connection management.

Redis is used across the application for caching, rate limiting,
conversation-session state, and background task coordination. A single
connection pool is created at startup and reused throughout the
process's lifetime.
"""

from __future__ import annotations

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


def get_redis_pool() -> ConnectionPool:
    """Return (lazily creating) the process-wide Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            str(settings.REDIS_URL),
            max_connections=50,
            decode_responses=True,
        )
    return _redis_pool


def get_redis_client() -> Redis:
    """Return (lazily creating) the process-wide async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(connection_pool=get_redis_pool())
    return _redis_client


async def check_redis_connection() -> bool:
    """Ping Redis to verify connectivity.

    Returns:
        ``True`` if the ``PING`` command succeeds, ``False`` otherwise.
    """
    try:
        client = get_redis_client()
        return await client.ping()
    except Exception:  # noqa: BLE001
        logger.exception("Redis connectivity check failed")
        return False


async def close_redis_connection() -> None:
    """Close the Redis client and connection pool on application shutdown."""
    global _redis_client, _redis_pool

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None

    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None

    logger.info("Redis connection closed")
