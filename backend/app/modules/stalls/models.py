"""ORM models for the `stalls` domain module.

Tables owned here (from `database/schema.sql`, Section 3: FOOD
STALLS & CATALOG — stall-level subset only; menu_categories /
menu_items are out of scope for this milestone):
    - stalls                  (a vendor's sellable food outlet)
    - stall_search_aliases    (normalized alternate names for a stall)
    - stall_operating_hours   (weekly recurring open/close schedule)

`stalls.campus_id` is intentionally NOT modeled here — it is derived
via `stalls.location_id -> locations.campus_id` to keep the schema
in 3NF, per `DATABASE_DECISIONS.md`. Do not add a `campus_id` column
or relationship to `Stall`.

Audit-trail-only foreign keys (`created_by`, `updated_by`,
`approved_by`) are modeled as plain `mapped_column(ForeignKey(...))`
without a corresponding `relationship()` — see
`app/modules/users/models.py` module docstring for the rationale.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum as PgEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import StallStatusEnum
from app.database.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.modules.location.models import Location
    from app.modules.users.models import Vendor


class Stall(SoftDeleteMixin, BaseModel):
    """A vendor's sellable food outlet.

    References a `location` rather than a block directly.
    """

    __tablename__ = "stalls"

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(170), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuisine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[StallStatusEnum] = mapped_column(
        PgEnum(
            StallStatusEnum,
            name="stall_status_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=StallStatusEnum.PENDING_APPROVAL,
        server_default="pending_approval",
    )
    is_accepting_orders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    rating_avg: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0, server_default="0"
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    # Audit-only FKs — no relationship() (see users/models.py docstring).
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="stalls")
    location: Mapped["Location"] = relationship("Location", back_populates="stalls")
    search_aliases: Mapped[list["StallSearchAlias"]] = relationship(
        "StallSearchAlias", back_populates="stall", cascade="all, delete-orphan"
    )
    operating_hours: Mapped[list["StallOperatingHours"]] = relationship(
        "StallOperatingHours", back_populates="stall", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uq_stalls_slug"),
        CheckConstraint("rating_avg BETWEEN 0 AND 5", name="ck_stalls_rating_avg"),
        CheckConstraint("rating_count >= 0", name="ck_stalls_rating_count"),
        Index("ix_stalls_vendor_id", "vendor_id"),
        Index("ix_stalls_location_id", "location_id"),
        Index("ix_stalls_status", "status", postgresql_where="deleted_at IS NULL"),
        Index("ix_stalls_deleted_at", "deleted_at"),
        Index(
            "ix_stalls_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Stall id={self.id} name={self.name} status={self.status}>"


class StallSearchAlias(BaseModel):
    """Normalized alternate names a student might use for a stall.

    e.g. "Burger Shop" / "Burger Point" / "Burger Stall" all resolve
    to one stall. One row per alias, not a JSON/array column, for the
    same reasons as `location_aliases`.

    Note: like `location_aliases`, this table has no `deleted_at`
    column, so this model does NOT use `SoftDeleteMixin`.
    """

    __tablename__ = "stall_search_aliases"

    stall_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stalls.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False)
    # Audit-only FK — no relationship() (see users/models.py docstring).
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    stall: Mapped["Stall"] = relationship("Stall", back_populates="search_aliases")

    __table_args__ = (
        UniqueConstraint("stall_id", "alias", name="uq_stall_search_aliases_stall_alias"),
        Index("ix_stall_search_aliases_stall_id", "stall_id"),
        Index(
            "ix_stall_search_aliases_alias_trgm",
            "alias",
            postgresql_using="gin",
            postgresql_ops={"alias": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StallSearchAlias id={self.id} alias={self.alias}>"


class StallOperatingHours(BaseModel):
    """Weekly recurring open/close schedule per stall.

    Split out of `stalls` (rather than a single opens_at/closes_at
    pair on the stall row) because different weekdays can have
    different hours — this normalization avoids update anomalies.

    Note: this table has no `deleted_at` column, so this model does
    NOT use `SoftDeleteMixin`.
    """

    __tablename__ = "stall_operating_hours"

    stall_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stalls.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 0 = Sunday ... 6 = Saturday.
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    opens_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    closes_at: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # --- Relationships ---
    stall: Mapped["Stall"] = relationship("Stall", back_populates="operating_hours")

    __table_args__ = (
        UniqueConstraint("stall_id", "day_of_week", name="uq_stall_hours_stall_day"),
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6", name="ck_stall_hours_day_of_week"
        ),
        CheckConstraint(
            "is_closed = TRUE OR "
            "(opens_at IS NOT NULL AND closes_at IS NOT NULL AND opens_at < closes_at)",
            name="ck_stall_hours_time_pair",
        ),
        Index("ix_stall_hours_stall_id", "stall_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StallOperatingHours stall_id={self.stall_id} day={self.day_of_week}>"