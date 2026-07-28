"""CampusBite AI — FastAPI application entrypoint.

Milestone 1 scope: application bootstrap and core infrastructure only.
No business routers are registered here yet — they will be included
module-by-module in future milestones via ``app.include_router(...)``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.engine import check_database_connection, dispose_engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.redis import check_redis_connection, close_redis_connection
from app.modules.auth.router import router as auth_router
from app.modules.vendors.router import router as vendors_router

settings = get_settings()

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown side effects.

    Startup:
        Verifies PostgreSQL and Redis connectivity so misconfiguration
        fails fast instead of surfacing on the first user request.

    Shutdown:
        Cleanly disposes of the database engine's connection pool and
        closes the Redis connection.
    """
    logger.info(
        "Starting %s [%s environment]",
        settings.PROJECT_NAME,
        settings.ENVIRONMENT.value,
    )

    db_ok = await check_database_connection()
    if db_ok:
        logger.info("PostgreSQL connection verified")
    else:
        logger.warning(
            "PostgreSQL connection could not be verified at startup. "
            "The application will continue starting, but database-backed "
            "features will fail until connectivity is restored."
        )

    redis_ok = await check_redis_connection()
    if redis_ok:
        logger.info("Redis connection verified")
    else:
        logger.warning(
            "Redis connection could not be verified at startup. "
            "The application will continue starting, but cache-backed "
            "features will fail until connectivity is restored."
        )

    yield

    logger.info("Shutting down %s", settings.PROJECT_NAME)
    await dispose_engine()
    await close_redis_connection()


def create_app() -> FastAPI:
    """Application factory.

    Building the app behind a factory function (rather than a bare
    module-level object) keeps the app importable and re-creatable in
    tests without triggering duplicate startup side effects.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "AI-powered, WhatsApp-first food pre-booking platform for "
            "university campuses. This API serves the WhatsApp Cloud "
            "API integration, the Stall Owner / Admin React dashboard, "
            "and future mobile and kiosk clients."
        ),
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)

    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(vendors_router, prefix=settings.API_V1_PREFIX)

    # NOTE: Remaining business module routers (stalls, bookings, admin,
    # ai, etc.) are intentionally NOT included yet. They will be wired
    # up as `app.include_router(...)` calls in their respective future
    # patches/milestones.

    @app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
    async def health_check() -> dict[str, object]:
        """Basic liveness/readiness probe.

        Reports process status plus PostgreSQL/Redis connectivity so
        orchestration tooling (Docker, Kubernetes, uptime monitors) can
        make accurate health decisions.
        """
        db_healthy = await check_database_connection()
        redis_healthy = await check_redis_connection()
        overall_status = "ok" if db_healthy and redis_healthy else "degraded"

        return {
            "status": overall_status,
            "project": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT.value,
            "dependencies": {
                "postgresql": "up" if db_healthy else "down",
                "redis": "up" if redis_healthy else "down",
            },
        }

    return app


app = create_app()
