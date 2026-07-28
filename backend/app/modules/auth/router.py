"""Authentication router.

Patch 1 introduced the authentication foundation.
Patch 2 added registration and login.
Patch 3 adds protected endpoints that demonstrate
authentication and role-based authorization.

Business logic lives in ``service.py``.
Authentication and authorization live in
``dependencies.py``.
This router only translates requests into service
calls and shapes HTTP responses.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.dependencies import (
    get_auth_service,
    get_current_user,
    require_admin,
    require_student,
    require_vendor,
)
from app.modules.auth.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    RegistrationNumberAlreadyExistsException,
)
from app.modules.auth.schemas import (
    AuthenticatedUserResponse,
    LoginRequest,
    LoginResponse,
    StudentRegisterRequest,
    VendorRegisterRequest,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/health", summary="Authentication module health check")
async def auth_health_check() -> dict[str, str]:
    """Report that the authentication module is mounted and importable.

    Does not check downstream dependencies (DB, Redis) — the
    project-wide ``/health`` endpoint in ``app.main`` already does
    that. This endpoint exists purely to confirm the auth router is
    wired up and reachable under ``/api/v1/auth``.
    """
    return {"status": "ok", "module": "authentication"}


@router.post(
    "/register/student",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
async def register_student(
    payload: StudentRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Create a student account and return an access token for it.

    Raises:
        HTTPException: 409 if the email or registration number is
            already registered.
    """
    try:
        user = await auth_service.register_student(payload)
    except EmailAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    except RegistrationNumberAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc

    return _issue_login_response(auth_service, user)


@router.post(
    "/register/vendor",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vendor account",
)
async def register_vendor(
    payload: VendorRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Create a vendor account and return an access token for it.

    Raises:
        HTTPException: 409 if the email is already registered.
    """
    try:
        user = await auth_service.register_vendor(payload)
    except EmailAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc

    return _issue_login_response(auth_service, user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in with email and password",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate a user and return an access token.

    Raises:
        HTTPException: 401 if the email/password pair is invalid.
            403 if the credentials are correct but the account is
            inactive or soft-deleted.
    """
    try:
        user = await auth_service.authenticate(payload)
    except InvalidCredentialsException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc

    return _issue_login_response(auth_service, user)


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
    summary="Get the current authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)) -> AuthenticatedUserResponse:
    """Return the authenticated caller's own profile.

    A pure read of the ``User`` already resolved by
    ``get_current_user`` — no additional database query and no writes.
    """
    return AuthenticatedUserResponse.model_validate(current_user)


@router.get("/me/student", summary="Student-role access check")
async def student_only(current_user: User = Depends(require_student)) -> dict[str, str]:
    """Confirm the caller is authenticated with the ``student`` role.

    Exists to exercise ``require_student`` end-to-end as a real
    protected route; the response carries no data beyond a static
    confirmation message.
    """
    return {
        "status": "ok",
        "message": f"Hello, student {current_user.full_name}. You are authorized.",
    }


@router.get("/me/vendor", summary="Vendor-role access check")
async def vendor_only(current_user: User = Depends(require_vendor)) -> dict[str, str]:
    """Confirm the caller is authenticated with the ``vendor`` role.

    Exists to exercise ``require_vendor`` end-to-end as a real
    protected route; the response carries no data beyond a static
    confirmation message.
    """
    return {
        "status": "ok",
        "message": f"Hello, vendor {current_user.full_name}. You are authorized.",
    }


@router.get("/me/admin", summary="Admin-role access check")
async def admin_only(current_user: User = Depends(require_admin)) -> dict[str, str]:
    """Confirm the caller is authenticated with the ``admin`` role.

    Exists to exercise ``require_admin`` end-to-end as a real
    protected route; the response carries no data beyond a static
    confirmation message.
    """
    return {
        "status": "ok",
        "message": f"Hello, admin {current_user.full_name}. You are authorized.",
    }


def _issue_login_response(auth_service: AuthService, user: User) -> LoginResponse:
    """Build the shared ``{access_token, token_type, user}`` response.

    Factored out so all three endpoints above shape their response
    identically, matching the Patch 2 spec's "same response" note for
    registration and login.
    """
    token = auth_service.issue_token_for_user(user)
    return LoginResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        user=AuthenticatedUserResponse.model_validate(user),
    )