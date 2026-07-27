"""Reusable SQLAlchemy declarative mixins.

Split out of the original `app/core/base_model.py` as part of the
`app/database/` infrastructure refactor. `base.py` composes these into
`Base` / `BaseModel`; individual modules may also mix them in directly
if a table needs a non-standard combination.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` audit timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds a ``deleted_at`` column to support soft deletion.

    Business modules that need soft-delete semantics should include this
    mixin explicitly; it is not applied globally.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Return ``True`` if the record has been soft-deleted."""
        return self.deleted_at is not None
