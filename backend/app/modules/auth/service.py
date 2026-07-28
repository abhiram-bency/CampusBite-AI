"""Vendor service.

Business logic only — no HTTP concerns, no raw SQL. Composes
`VendorRepository` to implement the Phase 1 vendor-profile use cases.
"""

from __future__ import annotations

from uuid import UUID

from app.core.logging import get_logger
from app.modules.users.models import User
from app.modules.vendors.exceptions import VendorProfileNotFoundError
from app.modules.vendors.repository import VendorRepository
from app.modules.vendors.schemas import VendorProfileResponse, VendorProfileUpdateRequest

logger = get_logger(__name__)


class VendorService:
    """Business logic for vendor profile viewing and self-service updates."""

    def __init__(self, repository: VendorRepository) -> None:
        """Initialize the service with its repository dependency.

        Args:
            repository: A `VendorRepository` instance, typically
                constructed per-request in `router.py`.
        """
        self._repository = repository

    async def get_own_profile(self, current_user: User) -> VendorProfileResponse:
        """Fetch the calling vendor's own profile.

        Args:
            current_user: The authenticated user (already confirmed to
                have the `vendor` role by the `require_vendor`
                dependency before this is called).

        Returns:
            The vendor's combined profile.

        Raises:
            VendorProfileNotFoundError: If no vendor profile exists
                for this user (should not happen in normal operation —
                see the exception's docstring).
        """
        vendor = await self._repository.get_vendor_by_user_id(current_user.id)
        if vendor is None:
            logger.warning(
                "Vendor-role user has no vendor profile row",
                extra={"extra_fields": {"user_id": str(current_user.id)}},
            )
            raise VendorProfileNotFoundError()

        return VendorProfileResponse.from_models(current_user, vendor)

    async def update_own_profile(
        self, current_user: User, payload: VendorProfileUpdateRequest
    ) -> VendorProfileResponse:
        """Apply a partial update to the calling vendor's own profile.

        Args:
            current_user: The authenticated vendor.
            payload: The fields to update; unset fields are left
                unchanged (see `VendorProfileUpdateRequest`).

        Returns:
            The updated vendor profile.

        Raises:
            VendorProfileNotFoundError: If no vendor profile exists
                for this user.
        """
        vendor = await self._repository.get_vendor_by_user_id(current_user.id)
        if vendor is None:
            raise VendorProfileNotFoundError()

        updates = payload.model_dump(    
            exclude_unset=True,
            exclude_none=True,
        )
        for field_name, value in updates.items():
            if field_name in ALLOWED_UPDATE_FIELDS:
                setattr(vendor, field_name, value)

        vendor = await self._repository.save(vendor)
        if updates:
            logger.info(
                "Vendor profile updated",
                extra={"extra_fields": {"user_id": str(current_user.id), "fields": list(updates)}},
            )

        return VendorProfileResponse.from_models(current_user, vendor)

    async def get_profile_for_admin(self, vendor_user_id: UUID) -> VendorProfileResponse:
        """Fetch any vendor's profile, for admin use.

        Args:
            vendor_user_id: The target vendor's `user_id`.

        Returns:
            The vendor's combined profile.

        Raises:
            VendorProfileNotFoundError: If `vendor_user_id` does not
                resolve to an existing, non-deleted vendor profile (or
                its owning user — the latter should be unreachable
                given the `vendors.user_id` foreign key, but is still
                checked explicitly rather than assumed).
        """
        vendor = await self._repository.get_vendor_by_user_id(vendor_user_id)
        if vendor is None:
            raise VendorProfileNotFoundError()

        user = await self._repository.get_user_by_id(vendor_user_id)
        if user is None:
            raise VendorProfileNotFoundError()

        return VendorProfileResponse.from_models(user, vendor)
