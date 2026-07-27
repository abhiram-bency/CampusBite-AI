"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Ensure each test starts with a freshly parsed :class:`Settings`."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings() -> Settings:
    """Provide a ``Settings`` instance pinned to the test environment."""
    return Settings(ENVIRONMENT="test", LOG_JSON=False, DEBUG=True)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an ``httpx.AsyncClient`` wired directly to the ASGI app.

    Uses ``ASGITransport`` so tests exercise the real FastAPI app
    (including lifespan and exception handlers) without binding a real
    network socket.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
