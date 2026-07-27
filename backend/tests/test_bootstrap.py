"""Milestone 1 smoke tests.

Verifies the application factory, configuration system, and health
endpoint are wired correctly. These tests intentionally avoid any
business logic since none exists yet.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import Settings, get_settings


def test_settings_load_defaults() -> None:
    """Settings should load with sane local defaults."""
    settings = Settings()
    assert settings.PROJECT_NAME == "CampusBite AI"
    assert settings.API_V1_PREFIX == "/api/v1"


def test_settings_are_cached() -> None:
    """`get_settings` should return the same cached instance."""
    first = get_settings()
    second = get_settings()
    assert first is second


def test_database_url_is_assembled_when_not_provided() -> None:
    """DATABASE_URL should be derived from POSTGRES_* components."""
    settings = Settings(DATABASE_URL=None)
    assert "postgresql+asyncpg" in str(settings.DATABASE_URL)


def test_redis_url_is_assembled_when_not_provided() -> None:
    """REDIS_URL should be derived from REDIS_* components."""
    settings = Settings(REDIS_URL=None)
    assert str(settings.REDIS_URL).startswith("redis://")


@pytest.mark.asyncio
async def test_health_endpoint_returns_status(async_client: AsyncClient) -> None:
    """The health endpoint should always return a status field."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert body["project"] == "CampusBite AI"
    assert "dependencies" in body
