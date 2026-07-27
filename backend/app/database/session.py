"""Async SQLAlchemy session management.

Moved from `app/core/database.py` as part of the `app/database/`
infrastructure refactor (engine/session split: `app/database/engine.py`
owns the engine; this module owns session creation).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.engine import engine

# ----------------------------------------------------------------------
# Session factory
# ----------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional-scoped ``AsyncSession``.

    Intended for use as a FastAPI dependency (see
    `app.core.dependencies.get_db`). Commits on success, rolls back on
    exception, and always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for use outside of FastAPI request handling.

    Useful in scripts, background jobs, and the AI tool-calling layer
    where a request-scoped dependency is not available.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
