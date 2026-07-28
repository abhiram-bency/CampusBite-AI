# app/modules/auth/security.py
"""Password hashing and JWT utilities for the authentication module.

Centralizes all password hashing and JWT encode/decode logic behind a
small set of pure functions. No other module should call ``passlib``
or ``jose`` directly — always go through this module so the hashing
scheme and token claims stay consistent everywhere they're used.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import ValidationError
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.logging import get_logger
from app.modules.auth.exceptions import InvalidTokenException
from app.modules.auth.schemas import TokenPayload
from app.modules.auth.utils import utcnow

logger = get_logger(__name__)
settings = get_settings()

# ----------------------------------------------------------------------
# Password hashing
# ----------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash, safe to persist in ``users.password_hash``.
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The plaintext password supplied by the caller.
        hashed_password: The bcrypt hash previously produced by
            :func:`hash_password`.

    Returns:
        ``True`` if the password matches, ``False`` otherwise. Never
        raises on a malformed hash — a malformed hash is treated as a
        non-match rather than an error.
    """
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        logger.warning("Password verification attempted against a malformed hash")
        return False


# ----------------------------------------------------------------------
# JWT
# ----------------------------------------------------------------------


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, object] | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The token subject (``sub`` claim) — the authenticated
            user's ``id`` as a string.
        role: The user's role (a ``user_role_enum`` value), embedded
            as a claim so downstream dependencies can authorize
            without a second database round-trip.
        expires_delta: Overrides the configured default expiry
            (``Settings.ACCESS_TOKEN_EXPIRE_MINUTES``) when provided.
        extra_claims: Additional claims to merge into the payload
            (e.g. a future ``campus_id`` claim). Reserved keys
            (``sub``, ``role``, ``iat``, ``exp``) are not overridable
            this way — they are always set from the typed parameters.

    Returns:
        The encoded JWT as a string.
    """
    now = utcnow()
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: dict[str, object] = dict(extra_claims or {})
    payload.update(
        {
            "sub": subject,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
    )

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token.

    Args:
        token: The encoded JWT, as received in the ``Authorization:
            Bearer <token>`` header.

    Returns:
        The validated token payload.

    Raises:
        InvalidTokenException: If the token is malformed, expired, or
            signed with an unexpected key/algorithm, or if its claims
            don't match the expected :class:`TokenPayload` shape.
    """
    try:
        raw_payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise InvalidTokenException() from exc

    try:
        return TokenPayload(**raw_payload)
    except ValidationError as exc:
        logger.debug("JWT payload failed schema validation: %s", exc)
        raise InvalidTokenException() from exc