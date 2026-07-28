"""Tests for the authentication module.

Covers password hashing, JWT issuance/validation, authentication
dependencies, and the authentication router's protected endpoints.

These tests target the current authentication implementation
(Patches 1–3).
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.exceptions import InvalidTokenException
from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.modules.users.models import User


# ---------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------


def test_hash_password_produces_bcrypt_hash() -> None:
    """Hashing should never return plaintext and should use bcrypt."""
    hashed = hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$2")
    assert hash_password("correct horse battery staple") != hashed


def test_verify_password_accepts_correct_password() -> None:
    """Correct password should verify."""
    hashed = hash_password("hunter2")

    assert verify_password("hunter2", hashed) is True


def test_verify_password_rejects_incorrect_password() -> None:
    """Wrong password should fail verification."""
    hashed = hash_password("hunter2")

    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_invalid_hash() -> None:
    """Malformed hashes should return False instead of raising."""
    assert verify_password("anything", "not-a-valid-bcrypt-hash") is False


# ---------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------


def test_create_and_decode_access_token_round_trip() -> None:
    """A freshly-created JWT should decode back to the original payload."""
    user_id = uuid.uuid4()

    token = create_access_token(
        subject=str(user_id),
        role="student",
    )

    payload = decode_access_token(token)

    assert payload.sub == str(user_id)
    assert payload.role.value == "student"
    assert isinstance(payload.iat, int)
    assert isinstance(payload.exp, int)


def test_decode_access_token_rejects_expired_token() -> None:
    """Expired tokens should be rejected."""
    token = create_access_token(
        subject=str(uuid.uuid4()),
        role="student",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(InvalidTokenException):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    """Garbage input should never decode successfully."""
    with pytest.raises(InvalidTokenException):
        decode_access_token("not-a-real-token")


# ---------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_health_endpoint(async_client: AsyncClient) -> None:
    """The auth health endpoint should always return OK."""
    response = await async_client.get("/api/v1/auth/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "authentication",
    }


# ---------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_requires_token() -> None:
    """Requests without Authorization should receive HTTP 401."""
    app = create_app()

    @app.get("/api/v1/_test/protected")
    async def protected(
        user: User = Depends(get_current_user),
    ) -> dict[str, str]:
        return {"id": str(user.id)}

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/_test/protected")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    """Malformed bearer tokens should receive HTTP 401."""
    app = create_app()

    @app.get("/api/v1/_test/protected")
    async def protected(
        user: User = Depends(get_current_user),
    ) -> dict[str, str]:
        return {"id": str(user.id)}

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/_test/protected",
            headers={
                "Authorization": "Bearer not-a-real-token",
            },
        )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


# ---------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_me_requires_authentication(
    async_client: AsyncClient,
) -> None:
    """GET /auth/me should reject anonymous callers."""
    response = await async_client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_student_only_requires_authentication(
    async_client: AsyncClient,
) -> None:
    """Student endpoint should reject anonymous callers."""
    response = await async_client.get("/api/v1/auth/student-only")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_vendor_only_requires_authentication(
    async_client: AsyncClient,
) -> None:
    """Vendor endpoint should reject anonymous callers."""
    response = await async_client.get("/api/v1/auth/vendor-only")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_only_requires_authentication(
    async_client: AsyncClient,
) -> None:
    """Admin endpoint should reject anonymous callers."""
    response = await async_client.get("/api/v1/auth/admin-only")

    assert response.status_code == 401