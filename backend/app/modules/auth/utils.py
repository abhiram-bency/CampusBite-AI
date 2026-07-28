"""Small, dependency-free helpers shared across the authentication module."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC ``datetime``.

    Centralized so every token timestamp (``iat`` / ``exp``) in this
    module comes from a single, consistent, timezone-aware clock
    source rather than each call site calling ``datetime.utcnow()``
    (naive) or ``datetime.now()`` (local-tz) independently.
    """
    return datetime.now(timezone.utc)