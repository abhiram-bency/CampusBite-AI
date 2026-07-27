# app/modules/users/models.py
"""ORM models for the `users` domain module.

Tables owned here (from `database/schema.sql`, Section 1: IDENTITY):
    - users     (root identity for every actor)
    - students  (1:1 extension of users)
    - vendors   (1:1 extension of users)
    - admins    (1:1 extension of users)

`students`, `vendors`, `admins` share `users.id` as their own primary
key (PK == FK), so they inherit `Base` + `TimestampMixin` (+
`SoftDeleteMixin` where the schema has `deleted_at`) directly rather
than `BaseModel` — `BaseModel` would generate an unwanted second
`id` column via `UUIDPrimaryKeyMixin`.

Audit-trail-only foreign keys (`created_by`, `updated_by`,
`verified_by`) are modeled as plain `mapped_column(ForeignKey(...))`
without a corresponding `relationship()`. They exist for
provenance/audit purposes, not for ORM traversal, and several tables
reference `users.id` more than once (e.g. a future `campuses` audit
FK for both `created_by` and `updated_by`) — adding `relationship()`
for every one of these would require disambiguating `foreign_keys=`
and `overlaps=` on both sides for no read benefit at this milestone.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Enum as PgEnum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AdminLevelEnum, FoodTypeEnum, UserRoleEnum
from app.database.base import Base, BaseModel, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.modules.campus.models import Campus
    from app.modules.stalls.models import Stall


class User(SoftDeleteMixin, BaseModel):
    """Root identity for every actor (student, vendor, admin).

    Role-specific attributes live in the 1:1 subtype tables below.
    """

    __tablename__ = "users"

    role: Mapped[UserRoleEnum] = mapped_column(
        PgEnum(
            UserRoleEnum,
            name="user_role_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    # NULL for WhatsApp-only students.
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # --- Relationships (1:1 identity subtypes) ---
    student: Mapped[Optional["Student"]] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    vendor: Mapped[Optional["Vendor"]] = relationship(
        "Vendor", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin: Mapped[Optional["Admin"]] = relationship(
        "Admin", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("phone_number", name="uq_users_phone_number"),
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            r"phone_number ~ '^\+?[0-9]{8,15}$'",
            name="ck_users_phone_number_format",
        ),
        Index("ix_users_role", "role", postgresql_where="deleted_at IS NULL"),
        Index("ix_users_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} role={self.role} phone={self.phone_number}>"


class Student(TimestampMixin, SoftDeleteMixin, Base):
    """Student-specific profile, 1:1 extension of `users`.

    `registration_number` is the primary login credential for
    WhatsApp.
    """

    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year_of_study: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    # Free-text, informal, e.g. "Block 34 Hostel".
    hostel_or_block: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Reuses food_type_enum; a student's general preference.
    dietary_preference: Mapped[Optional[FoodTypeEnum]] = mapped_column(
        PgEnum(
            FoodTypeEnum,
            name="food_type_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="student")
    campus: Mapped["Campus"] = relationship("Campus", back_populates="students")

    __table_args__ = (
        UniqueConstraint("registration_number", name="uq_students_registration_number"),
        CheckConstraint(
            "year_of_study BETWEEN 1 AND 8", name="ck_students_year_of_study"
        ),
        Index("ix_students_campus_id", "campus_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student user_id={self.user_id} reg_no={self.registration_number}>"


class Vendor(TimestampMixin, SoftDeleteMixin, Base):
    """Vendor (stall owner) profile, 1:1 extension of `users`."""

    __tablename__ = "vendors"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    business_name: Mapped[str] = mapped_column(String(150), nullable=False)
    business_registration_no: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    # Audit-only FK — no relationship() (see module docstring).
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="vendor")
    stalls: Mapped[list["Stall"]] = relationship("Stall", back_populates="vendor")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Vendor user_id={self.user_id} business={self.business_name}>"


class Admin(TimestampMixin, SoftDeleteMixin, Base):
    """Administrator profile, 1:1 extension of `users`."""

    __tablename__ = "admins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    admin_level: Mapped[AdminLevelEnum] = mapped_column(
        PgEnum(
            AdminLevelEnum,
            name="admin_level_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=AdminLevelEnum.CAMPUS_ADMIN,
        server_default="campus_admin",
    )
    # NULL => all campuses (super_admin).
    campus_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campuses.id", ondelete="SET NULL"), nullable=True
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="admin")
    campus: Mapped[Optional["Campus"]] = relationship("Campus", back_populates="admins")

    __table_args__ = (
        CheckConstraint(
            "admin_level <> 'super_admin' OR campus_id IS NULL",
            name="ck_admins_super_admin_no_campus",
        ),
        Index("ix_admins_campus_id", "campus_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Admin user_id={self.user_id} level={self.admin_level}>"