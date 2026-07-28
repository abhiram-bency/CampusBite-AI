"""FastAPI dependencies for the authentication module.

``get_current_user`` and the ``require_*`` role guards are the only
dependencies other modules should import. Login is not implemented
yet (a later patch), so nothing issues a token — but the validation
path is fully implemented now so other modules can build protected
routes against a stable contract immediately, and so Patch 2 only has
to add token *issuance*, not validation.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import UserRoleEnum
from app.database.session import get_session
from app.modules.auth.exceptions import (
    InactiveUserException,
    InsufficientPermissionsException,
    InvalidTokenException,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.security import decode_access_token
from app.modules.auth.service import AuthService
from app.modules.users.models import User

settings = get_settings()

# Points at the future login endpoint (added in a later auth patch).
# Declaring the URL now means Swagger's "Authorize" flow starts working
# the moment `/auth/login` exists, with no change needed here.
# `auto_error=False` lets `get_current_user` return a uniform 401
# (rather than FastAPI's default 403) when no token is presented.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Construct an ``AuthService`` bound to the request's DB session."""
    return AuthService(AuthRepository(session))


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Resolve the authenticated ``User`` from the request's bearer token.

    Raises:
        HTTPException: 401 if no token is presented, the token is
            invalid/expired, or the referenced user no longer exists.
            403 if the referenced user exists but is inactive or
            soft-deleted.
    """
    if token is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        payload = decode_access_token(token)
    except InvalidTokenException as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        _ensure_active(user)
    except InactiveUserException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    return user


def _ensure_active(user: User) -> None:
    """Raise ``InactiveUserException`` if the user is inactive or soft-deleted."""
    if not user.is_active or user.deleted_at is not None:
        raise InactiveUserException()


def _require_role(required_role: UserRoleEnum):
    """Build a dependency requiring ``current_user.role == required_role``."""

    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=InsufficientPermissionsException().message,
            )
        return current_user

    return _dependency


require_student = _require_role(UserRoleEnum.STUDENT)
require_vendor = _require_role(UserRoleEnum.VENDOR)
require_admin = _require_role(UserRoleEnum.ADMIN)