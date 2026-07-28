"""Vendor module exceptions.

Extends the project-wide exception hierarchy in `app.core.exceptions`
(the same pattern `app.modules.auth.exceptions` follows) so the
existing centralized handlers in `app.main` handle these consistently.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import NotFoundError


class VendorProfileNotFoundError(NotFoundError):
    """Raised when a vendor profile does not exist for a given user.

    In normal operation this should be unreachable for `/vendors/me`
    (a `vendor`-role user is only issued a token after
    `register_vendor` creates their profile row), but the case is
    still handled explicitly because accounts may be deleted or become
    inconsistent after a token has already been issued.
    """

    error_code = "vendor_profile_not_found"

    def __init__(
        self, message: str = "No vendor profile exists for this account.", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
