# app/modules/location/models.py
"""ORM models for the `location` domain module.

Tables owned here (from `database/schema.sql`, Section 2: CAMPUS
LOCATIONS):
    - locations         (flexible campus-position model)
    - location_aliases  (normalized alternate names for a location)

Audit-trail-only foreign keys (`created_by`, `updated_by`) are
modeled as plain `mapped_column(ForeignKey(...))` without a
corresponding `relationship()` — see `app/modules/users/models.py`
module docstring for the rationale.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Enum as PgEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import LocationTypeEnum
from app.database.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.modules.campus.models import Campus
    from app.modules.stalls.models import Stall


class Location(SoftDeleteMixin, BaseModel):
    """Flexible campus-position model.

    Deliberately NOT modeled as "stalls belong to a block" — many
    stalls sit near, outside, or opposite a block rather than inside
    one. `location_type` plus the free-text `reference_label` capture
    that informal relationship, while `latitude`/`longitude` allow a
    precise pin once available.
    """

    __tablename__ = "locations"

    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location_type: Mapped[LocationTypeEnum] = mapped_column(
        PgEnum(
            LocationTypeEnum,
            name="location_type_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    # e.g. "Block 34", "University Mall".
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # e.g. "Near Block 34", "Opposite Block 55".
    reference_label: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Future precise geolocation.
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    # Audit-only FKs — no relationship() (see users/models.py docstring).
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    campus: Mapped["Campus"] = relationship("Campus", back_populates="locations")
    aliases: Mapped[list["LocationAlias"]] = relationship(
        "LocationAlias", back_populates="location", cascade="all, delete-orphan"
    )
    stalls: Mapped[list["Stall"]] = relationship("Stall", back_populates="location")

    __table_args__ = (
        UniqueConstraint("campus_id", "name", name="uq_locations_campus_name"),
        CheckConstraint(
            "latitude IS NULL OR (latitude BETWEEN -90 AND 90)",
            name="ck_locations_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude BETWEEN -180 AND 180)",
            name="ck_locations_longitude",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_locations_lat_lng_pair",
        ),
        Index("ix_locations_campus_id", "campus_id"),
        Index("ix_locations_campus_type", "campus_id", "location_type"),
        Index(
            "ix_locations_coordinates",
            "latitude",
            "longitude",
            postgresql_where="latitude IS NOT NULL AND longitude IS NOT NULL",
        ),
        Index("ix_locations_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Location id={self.id} name={self.name}>"


class LocationAlias(BaseModel):
    """Normalized alternate names/spellings for a location.

    e.g. "Lib" / "Library Block" / "Central Library" all resolve to
    one `locations` row. Explicitly NOT a JSON/array column — one row
    per alias — so each alias can be indexed and queried directly.

    Note: unlike most tables in this schema, `location_aliases` has
    no `deleted_at` column, so this model does NOT use
    `SoftDeleteMixin` — only `TimestampMixin` (bundled via
    `BaseModel`).
    """

    __tablename__ = "location_aliases"

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False)
    # Audit-only FK — no relationship() (see users/models.py docstring).
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    location: Mapped["Location"] = relationship("Location", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("location_id", "alias", name="uq_location_aliases_location_alias"),
        Index("ix_location_aliases_location_id", "location_id"),
        Index(
            "ix_location_aliases_alias_trgm",
            "alias",
            postgresql_using="gin",
            postgresql_ops={"alias": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LocationAlias id={self.id} alias={self.alias}>"