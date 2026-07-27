# app/modules/campus/models.py
"""ORM models for the `campus` domain module.

Tables owned here (from `database/schema.sql`, Section 1: IDENTITY):
    - campuses  (tenant root for multi-campus support)

Audit-trail-only foreign keys (`created_by`, `updated_by`) are
modeled as plain `mapped_column(ForeignKey(...))` without a
corresponding `relationship()` — see `app/modules/users/models.py`
module docstring for the rationale.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.modules.location.models import Location
    from app.modules.users.models import Admin, Student


class Campus(SoftDeleteMixin, BaseModel):
    """Tenant root for multi-campus support."""

    __tablename__ = "campuses"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Short code, e.g. "MAIN".
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Asia/Kolkata", server_default="Asia/Kolkata"
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    # Audit-only FKs — no relationship() (see users/models.py docstring).
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    students: Mapped[list["Student"]] = relationship("Student", back_populates="campus")
    admins: Mapped[list["Admin"]] = relationship("Admin", back_populates="campus")
    locations: Mapped[list["Location"]] = relationship("Location", back_populates="campus")

    __table_args__ = (
        UniqueConstraint("code", name="uq_campuses_code"),
        Index("ix_campuses_deleted_at", "deleted_at"),
        Index(
            "ix_campuses_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Campus id={self.id} code={self.code}>"