"""Authentication schemas.

``Token`` / ``TokenPayload`` were introduced in Patch 1 (JWT internals).
This patch (Patch 2) adds the registration/login request and response
schemas. ``RegisterRequest`` / ``ForgotPassword`` / ``ResetPassword``
generics were never created — registration is role-specific
(``StudentRegisterRequest`` / ``VendorRegisterRequest``), and password
reset remains out of scope per the Patch 2 spec.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)

from app.core.enums import UserRoleEnum

# Matches the `users` table's `ck_users_phone_number_format` check
# constraint exactly, so a malformed number is rejected with a 422 at
# the request-schema boundary instead of surfacing as a raw database
# error.
_PHONE_NUMBER_PATTERN = r"^\+?[0-9]{8,15}$"


class Token(BaseModel):
    """Response body for a standalone token issuance.

    Not returned directly by any endpoint — registration and login
    both return the richer :class:`LoginResponse`, which wraps this
    same ``access_token`` / ``token_type`` shape alongside the user.
    """

    access_token: str = Field(
        ..., description="The signed JWT access token."
    )
    token_type: str = Field(
        default="bearer",
        description="RFC 6749 token type.",
    )


class TokenPayload(BaseModel):
    """Decoded JWT claim set.

    Mirrors exactly what
    :func:`app.modules.auth.security.create_access_token`
    encodes, so
    :func:`app.modules.auth.security.decode_access_token`
    can validate a raw payload against this schema.
    """

    sub: str = Field(
        ...,
        description="Subject claim — the user's `id` (UUID) as a string.",
    )
    role: UserRoleEnum = Field(
        ...,
        description="The user's role at token-issuance time.",
    )
    iat: int = Field(
        ...,
        description="Issued-at, Unix timestamp (UTC).",
    )
    exp: int = Field(
        ...,
        description="Expiry, Unix timestamp (UTC).",
    )


class _EmailNormalizingModel(BaseModel):
    """Base class for request schemas that carry an ``email`` field.

    Strips leading/trailing whitespace from every string field
    (``str_strip_whitespace``) and lowercases ``email`` specifically,
    so every write path (registration) and every read path (login,
    repository lookups) agree on one canonical form.
    ``AuthRepository.get_user_by_email`` / ``email_exists`` rely on
    this and do a direct match rather than re-normalizing.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("email", mode="after", check_fields=False)
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.lower()


class StudentRegisterRequest(_EmailNormalizingModel):
    """Request body for ``POST /auth/register/student``."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    email: EmailStr

    password: SecretStr = Field(
        ...,
        min_length=8,
        description="Plaintext password, minimum 8 characters.",
    )

    registration_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    phone_number: str = Field(
        ...,
        pattern=_PHONE_NUMBER_PATTERN,
        description=(
            "Required. `users.phone_number` is NOT NULL and UNIQUE in the "
            "frozen schema, so this cannot be optional without a schema "
            "migration."
        ),
    )

    campus_id: UUID


class VendorRegisterRequest(_EmailNormalizingModel):
    """Request body for ``POST /auth/register/vendor``."""

    business_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    owner_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    email: EmailStr

    password: SecretStr = Field(
        ...,
        min_length=8,
        description="Plaintext password, minimum 8 characters.",
    )

    phone_number: str = Field(
        ...,
        pattern=_PHONE_NUMBER_PATTERN,
    )


class LoginRequest(_EmailNormalizingModel):
    """Request body for ``POST /auth/login``."""

    email: EmailStr

    password: SecretStr = Field(
        ...,
        min_length=8,
    )


class AuthenticatedUserResponse(BaseModel):
    """Public-facing representation of the authenticated ``User``."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRoleEnum
    email: str | None
    full_name: str
    phone_number: str


class LoginResponse(BaseModel):
    """Response body shared by registration and login endpoints.

    Registration and login return the identical shape per the Patch 2
    spec ("same response"), so this one schema backs

    - ``POST /auth/register/student``
    - ``POST /auth/register/vendor``
    - ``POST /auth/login``
    """

    access_token: str
    token_type: str = "bearer"
    user: AuthenticatedUserResponse