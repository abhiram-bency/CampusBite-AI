"""Vendor repository.

Database access only — no business rules. Deliberately includes its
own `get_user_by_id` (rather than importing
`app.modules.auth.repository.AuthRepository`) so this module has no
cross-module repository dependency and stays independently testable,
per the project's module-independence rule.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, Vendor


class VendorRepository:
    """Database access for vendor profiles."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a request-scoped session.

        Args:
            session: Request-scoped AsyncSession injected by
            app.database.session.get_session.
        """
        self._session = session

    async def get_vendor_by_user_id(self, user_id: UUID) -> Vendor | None:
        """Fetch a vendor profile by its owning user's id.

        Excludes soft-deleted vendor profiles.

        Args:
            user_id: The vendor's `user_id` (== `users.id`).

        Returns:
            The matching `Vendor`, or `None` if not found or deleted.
        """
        stmt = (
            select(Vendor)
            .where(
                Vendor.user_id == user_id,
                Vendor.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by primary key.

        Excludes soft-deleted users. Used to assemble the identity
        half of a `VendorProfileResponse` when an admin looks up a
        vendor other than themselves.

        Args:
            user_id: The user's `id`.

        Returns:
            The matching `User`, or `None` if not found or deleted.
        """
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, vendor: Vendor) -> Vendor:
        """Persist pending changes to a `Vendor` instance.

        Args:
            vendor: A `Vendor` instance already attached to this
                repository's session, with attributes mutated by the
                caller (the service layer).

        Returns:
            The same `Vendor`, refreshed with database-generated
            values (e.g. `updated_at`).
        """
        await self._session.flush()
        await self._session.refresh(
            vendor,
            attribute_names=[
                "updated_at",
            ],
        )
        return vendor
