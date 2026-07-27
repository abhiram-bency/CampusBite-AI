"""CLI utility to verify PostgreSQL and Redis connectivity.

Usage:
    python -m scripts.check_infra

Exits with status code 0 if both services are reachable, 1 otherwise.
Useful in CI and local onboarding to fail fast with a clear message
instead of a confusing stack trace from the application itself.
"""

from __future__ import annotations

import asyncio
import sys

from app.database.engine import check_database_connection, dispose_engine
from app.core.logging import configure_logging, get_logger
from app.core.redis import check_redis_connection, close_redis_connection

configure_logging()
logger = get_logger(__name__)


async def main() -> int:
    """Check PostgreSQL and Redis connectivity and report the result."""
    db_ok = await check_database_connection()
    redis_ok = await check_redis_connection()

    logger.info("PostgreSQL: %s", "OK" if db_ok else "FAILED")
    logger.info("Redis: %s", "OK" if redis_ok else "FAILED")

    await dispose_engine()
    await close_redis_connection()

    return 0 if (db_ok and redis_ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
