"""Shared Python enum definitions mirroring PostgreSQL ENUM types.

These enums MUST stay in exact 1:1 sync with `database/enums.sql`
(member values, not member names, are what hit the wire — the DB
enum labels are lowercase snake_case strings).

`enums.sql` is the source of truth. This module is the ORM/typing
mirror of it. Do not redefine these enums inside individual domain
modules — several enums here are shared across modules (e.g.
`FoodTypeEnum` is used by both `students.dietary_preference` in the
users module and, in a future milestone, `menu_items.food_type` in
the catalog module) and a single shared definition avoids duplicate
`CREATE TYPE` conflicts and import ambiguity.

Only the enums required by domains implemented so far are defined
here. Add new enums as later milestones introduce the tables that
use them — do not pre-declare enums for out-of-scope domains
(orders, payments, inventory, menu, notifications, conversation,
AI, analytics).
"""

from __future__ import annotations

from enum import Enum


class UserRoleEnum(str, Enum):
    """Mirrors `user_role_enum`. Top-level role of a `users` row."""

    STUDENT = "student"
    VENDOR = "vendor"
    ADMIN = "admin"


class AdminLevelEnum(str, Enum):
    """Mirrors `admin_level_enum`. Administrative privilege tier."""

    SUPER_ADMIN = "super_admin"
    CAMPUS_ADMIN = "campus_admin"
    SUPPORT_STAFF = "support_staff"


class LocationTypeEnum(str, Enum):
    """Mirrors `location_type_enum`. How a `locations` row is positioned."""

    BLOCK = "block"
    NEARBY_BLOCK = "nearby_block"
    BUILDING = "building"
    LANDMARK = "landmark"
    OUTDOOR_AREA = "outdoor_area"
    OPEN_SPACE = "open_space"


class StallStatusEnum(str, Enum):
    """Mirrors `stall_status_enum`. Lifecycle status of a food stall."""

    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED_TEMPORARILY = "closed_temporarily"


class FoodTypeEnum(str, Enum):
    """Mirrors `food_type_enum`. Dietary classification.

    Used here for `students.dietary_preference` (a student's general
    preference). Also reused by `menu_items.food_type` in a later
    (catalog) milestone — defined once, here, to avoid duplication.
    """

    VEG = "veg"
    NON_VEG = "non_veg"
    EGG = "egg"
    VEGAN = "vegan"