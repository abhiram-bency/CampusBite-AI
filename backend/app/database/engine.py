"""Async SQLAlchemy engine management.

Moved from `app/core/database.py` as part of the `app/database/`
infrastructure refactor (engine/session split: this module owns the
engine itself; `app/database/session.py` owns session creation).

Exposes a single, process-wide async engine used by every business
module through the Repository layer — modules never construct an
engine themselves.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# ----------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO_SQL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    future=True,
)


async def check_database_connection() -> bool:
    """Ping the database to verify connectivity.

    Used by the FastAPI lifespan startup hook and the `/health`
    endpoint in `app.main`.

    Returns:
        ``True`` if a trivial query succeeds, ``False`` otherwise.
    """
    from sqlalchemy import text

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Database connectivity check failed")
        return False


async def dispose_engine() -> None:
    """Dispose of the engine's connection pool on application shutdown.

    Called from the FastAPI lifespan shutdown hook in `app.main`.
    """
    await engine.dispose()
    logger.info("Database engine disposed")
