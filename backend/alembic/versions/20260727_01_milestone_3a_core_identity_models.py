"""Milestone 3A: core database foundation & identity models.

Creates the tables, enum types, indexes, constraints, and
`updated_at` triggers for:
    - users, students, vendors, admins
    - campuses
    - locations, location_aliases
    - stalls, stall_search_aliases, stall_operating_hours

Source of truth: database/schema.sql (Sections 1-3, identity/campus/
location/stall subset only) and database/enums.sql.

Revision ID: 20260727_01
Revises: <UPDATE THIS>
Create Date: 2026-07-27

IMPORTANT: `down_revision` below is set to `None` because this
migration was authored without visibility into the project's actual
`alembic/versions/` history (only `alembic.ini` / `env.py` /
`versions/` were described as already existing, not their content).
If a prior baseline/init migration already exists in this project,
update `down_revision` to that revision's ID before running
`alembic upgrade head` — do NOT leave two head revisions.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# --- Alembic identifiers ---
revision: str = "20260727_01"
down_revision: Union[str, None] = None  # TODO: set to the existing baseline revision ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------
# Enum type definitions (must match database/enums.sql exactly)
# ---------------------------------------------------------------------

user_role_enum = postgresql.ENUM(
    "student", "vendor", "admin", name="user_role_enum", create_type=False
)
admin_level_enum = postgresql.ENUM(
    "super_admin", "campus_admin", "support_staff", name="admin_level_enum", create_type=False
)
location_type_enum = postgresql.ENUM(
    "block",
    "nearby_block",
    "building",
    "landmark",
    "outdoor_area",
    "open_space",
    name="location_type_enum",
    create_type=False,
)
stall_status_enum = postgresql.ENUM(
    "pending_approval",
    "active",
    "inactive",
    "suspended",
    "closed_temporarily",
    name="stall_status_enum",
    create_type=False,
)
food_type_enum = postgresql.ENUM(
    "veg", "non_veg", "egg", "vegan", name="food_type_enum", create_type=False
)

_ALL_ENUMS = [
    user_role_enum,
    admin_level_enum,
    location_type_enum,
    stall_status_enum,
    food_type_enum,
]


def upgrade() -> None:
    bind = op.get_bind()

    # -------------------------------------------------------------
    # Extensions (only those required by tables in this milestone;
    # `vector` is deferred to the milestone that introduces
    # embeddings tables).
    # -------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # -------------------------------------------------------------
    # Shared trigger function: keep `updated_at` current on UPDATE.
    # -------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # -------------------------------------------------------------
    # Enum types
    # -------------------------------------------------------------
    for enum_type in _ALL_ENUMS:
        enum_type.create(bind, checkfirst=True)

    # -------------------------------------------------------------
    # users
    # -------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("phone_number", name="uq_users_phone_number"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            r"phone_number ~ '^\+?[0-9]{8,15}$'", name="ck_users_phone_number_format"
        ),
    )
    op.create_index(
        "ix_users_role", "users", ["role"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])
    op.execute(
        "CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # campuses
    # -------------------------------------------------------------
    op.create_table(
        "campuses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'Asia/Kolkata'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("code", name="uq_campuses_code"),
    )
    op.create_index("ix_campuses_deleted_at", "campuses", ["deleted_at"])
    op.create_index(
        "ix_campuses_name_trgm",
        "campuses",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.execute(
        "CREATE TRIGGER trg_campuses_updated_at BEFORE UPDATE ON campuses "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # students
    # -------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campuses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("registration_number", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("year_of_study", sa.SmallInteger(), nullable=True),
        sa.Column("hostel_or_block", sa.String(length=100), nullable=True),
        sa.Column("dietary_preference", food_type_enum, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("registration_number", name="uq_students_registration_number"),
        sa.CheckConstraint("year_of_study BETWEEN 1 AND 8", name="ck_students_year_of_study"),
    )
    op.create_index("ix_students_campus_id", "students", ["campus_id"])
    op.execute(
        "CREATE TRIGGER trg_students_updated_at BEFORE UPDATE ON students "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # vendors
    # -------------------------------------------------------------
    op.create_table(
        "vendors",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("business_name", sa.String(length=150), nullable=False),
        sa.Column("business_registration_no", sa.String(length=100), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "CREATE TRIGGER trg_vendors_updated_at BEFORE UPDATE ON vendors "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # admins
    # -------------------------------------------------------------
    op.create_table(
        "admins",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "admin_level",
            admin_level_enum,
            nullable=False,
            server_default=sa.text("'campus_admin'"),
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "admin_level <> 'super_admin' OR campus_id IS NULL",
            name="ck_admins_super_admin_no_campus",
        ),
    )
    op.create_index("ix_admins_campus_id", "admins", ["campus_id"])
    op.execute(
        "CREATE TRIGGER trg_admins_updated_at BEFORE UPDATE ON admins "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # locations
    # -------------------------------------------------------------
    op.create_table(
        "locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campuses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("location_type", location_type_enum, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("reference_label", sa.String(length=150), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("floor", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("campus_id", "name", name="uq_locations_campus_name"),
        sa.CheckConstraint(
            "latitude IS NULL OR (latitude BETWEEN -90 AND 90)", name="ck_locations_latitude"
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR (longitude BETWEEN -180 AND 180)",
            name="ck_locations_longitude",
        ),
        sa.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_locations_lat_lng_pair",
        ),
    )
    op.create_index("ix_locations_campus_id", "locations", ["campus_id"])
    op.create_index("ix_locations_campus_type", "locations", ["campus_id", "location_type"])
    op.create_index(
        "ix_locations_coordinates",
        "locations",
        ["latitude", "longitude"],
        postgresql_where=sa.text("latitude IS NOT NULL AND longitude IS NOT NULL"),
    )
    op.create_index("ix_locations_deleted_at", "locations", ["deleted_at"])
    op.execute(
        "CREATE TRIGGER trg_locations_updated_at BEFORE UPDATE ON locations "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # location_aliases
    # -------------------------------------------------------------
    op.create_table(
        "location_aliases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(length=150), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("location_id", "alias", name="uq_location_aliases_location_alias"),
    )
    op.create_index("ix_location_aliases_location_id", "location_aliases", ["location_id"])
    op.create_index(
        "ix_location_aliases_alias_trgm",
        "location_aliases",
        ["alias"],
        postgresql_using="gin",
        postgresql_ops={"alias": "gin_trgm_ops"},
    )
    op.execute(
        "CREATE TRIGGER trg_location_aliases_updated_at BEFORE UPDATE ON location_aliases "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # stalls
    # -------------------------------------------------------------
    op.create_table(
        "stalls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vendors.user_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=170), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cuisine_type", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            stall_status_enum,
            nullable=False,
            server_default=sa.text("'pending_approval'"),
        ),
        sa.Column(
            "is_accepting_orders", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "rating_avg", sa.Numeric(3, 2), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("slug", name="uq_stalls_slug"),
        sa.CheckConstraint("rating_avg BETWEEN 0 AND 5", name="ck_stalls_rating_avg"),
        sa.CheckConstraint("rating_count >= 0", name="ck_stalls_rating_count"),
    )
    op.create_index("ix_stalls_vendor_id", "stalls", ["vendor_id"])
    op.create_index("ix_stalls_location_id", "stalls", ["location_id"])
    op.create_index(
        "ix_stalls_status", "stalls", ["status"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index("ix_stalls_deleted_at", "stalls", ["deleted_at"])
    op.create_index(
        "ix_stalls_name_trgm",
        "stalls",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.execute(
        "CREATE TRIGGER trg_stalls_updated_at BEFORE UPDATE ON stalls "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # stall_search_aliases
    # -------------------------------------------------------------
    op.create_table(
        "stall_search_aliases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "stall_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stalls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(length=150), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("stall_id", "alias", name="uq_stall_search_aliases_stall_alias"),
    )
    op.create_index("ix_stall_search_aliases_stall_id", "stall_search_aliases", ["stall_id"])
    op.create_index(
        "ix_stall_search_aliases_alias_trgm",
        "stall_search_aliases",
        ["alias"],
        postgresql_using="gin",
        postgresql_ops={"alias": "gin_trgm_ops"},
    )
    op.execute(
        "CREATE TRIGGER trg_stall_search_aliases_updated_at "
        "BEFORE UPDATE ON stall_search_aliases "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )

    # -------------------------------------------------------------
    # stall_operating_hours
    # -------------------------------------------------------------
    op.create_table(
        "stall_operating_hours",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "stall_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stalls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=True),
        sa.Column("closes_at", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("stall_id", "day_of_week", name="uq_stall_hours_stall_day"),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_stall_hours_day_of_week"),
        sa.CheckConstraint(
            "is_closed = TRUE OR "
            "(opens_at IS NOT NULL AND closes_at IS NOT NULL AND opens_at < closes_at)",
            name="ck_stall_hours_time_pair",
        ),
    )
    op.create_index("ix_stall_hours_stall_id", "stall_operating_hours", ["stall_id"])
    op.execute(
        "CREATE TRIGGER trg_stall_hours_updated_at BEFORE UPDATE ON stall_operating_hours "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Drop tables in reverse dependency order (triggers/indexes drop
    # automatically with their table).
    op.drop_table("stall_operating_hours")
    op.drop_table("stall_search_aliases")
    op.drop_table("stalls")
    op.drop_table("location_aliases")
    op.drop_table("locations")
    op.drop_table("admins")
    op.drop_table("vendors")
    op.drop_table("students")
    op.drop_table("campuses")
    op.drop_table("users")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    for enum_type in reversed(_ALL_ENUMS):
        enum_type.drop(bind, checkfirst=True)

    # Extensions are intentionally NOT dropped — other parts of the
    # database (or a concurrently running migration branch) may still
    # depend on pgcrypto / pg_trgm.