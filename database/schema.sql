-- =====================================================================
-- CampusBite AI — Database Schema
-- Milestone 2 (Revised / FINAL): Database Architecture
--
-- Load order: enums.sql, then this file.
--
-- This is a DESIGN ARTIFACT. It is NOT wired into Alembic yet —
-- model/migration generation is a future milestone. This revision
-- supersedes the prior schema.sql. See DATABASE_DECISIONS.md
-- §"Revision notes" for a full diff against the previous version.
--
-- Conventions:
--   - UUID primary keys (gen_random_uuid()), matching the completed
--     app/database/base.py / mixins.py infrastructure.
--   - TIMESTAMPTZ audit columns: created_at, updated_at (auto-kept
--     current via set_updated_at()), plus created_by / updated_by
--     (FK -> users.id) on tables a human vendor/admin edits.
--   - Soft delete via nullable deleted_at on master/reference tables
--     only — never on transactional or append-only log tables.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";      -- semantic embeddings (menu items, FAQ)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- trigram fuzzy/NL search on names + aliases

-- ---------------------------------------------------------------------
-- Shared trigger function: keep `updated_at` current on every UPDATE.
-- ---------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- SECTION 1: IDENTITY
-- =====================================================================

-- ---------------------------------------------------------------------
-- users
-- Purpose: single root identity for every actor (student, vendor,
-- admin). Role-specific attributes live in 1:1 subtype tables below.
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role                user_role_enum NOT NULL,
    phone_number        VARCHAR(20) NOT NULL,
    email               VARCHAR(255),
    full_name           VARCHAR(150) NOT NULL,
    password_hash       VARCHAR(255),           -- NULL for WhatsApp-only students
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    phone_verified_at   TIMESTAMPTZ,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_users_phone_number UNIQUE (phone_number),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_phone_number_format CHECK (phone_number ~ '^\+?[0-9]{8,15}$')
);

CREATE INDEX ix_users_role ON users (role) WHERE deleted_at IS NULL;
CREATE INDEX ix_users_deleted_at ON users (deleted_at);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- TODO(milestone: auth): OTP / WhatsApp session token tables are
-- intentionally deferred to the authentication milestone.


-- ---------------------------------------------------------------------
-- campuses
-- Purpose: tenant root for multi-campus support.
-- ---------------------------------------------------------------------
CREATE TABLE campuses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(150) NOT NULL,
    code                VARCHAR(20) NOT NULL,     -- short code, e.g. "MAIN"
    address             TEXT,
    timezone            VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_campuses_code UNIQUE (code)
);

-- Campus search (by name/code).
CREATE INDEX ix_campuses_deleted_at ON campuses (deleted_at);
CREATE INDEX ix_campuses_name_trgm ON campuses USING gin (name gin_trgm_ops);

CREATE TRIGGER trg_campuses_updated_at
    BEFORE UPDATE ON campuses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- students
-- Purpose: student-specific profile, 1:1 extension of `users`.
-- Registration number is the primary login credential for WhatsApp.
-- ---------------------------------------------------------------------
CREATE TABLE students (
    user_id             UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    campus_id           UUID NOT NULL REFERENCES campuses (id) ON DELETE RESTRICT,
    registration_number VARCHAR(50) NOT NULL,
    department          VARCHAR(100),
    year_of_study       SMALLINT,
    hostel_or_block     VARCHAR(100),             -- free-text, informal ("Block 34 Hostel")
    dietary_preference  food_type_enum,             -- reuses food_type_enum; a student's general preference
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_students_registration_number UNIQUE (registration_number),
    CONSTRAINT ck_students_year_of_study CHECK (year_of_study BETWEEN 1 AND 8)
);

CREATE INDEX ix_students_campus_id ON students (campus_id);

CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- vendors
-- Purpose: vendor (stall owner) profile, 1:1 extension of `users`.
-- ---------------------------------------------------------------------
CREATE TABLE vendors (
    user_id                     UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    business_name               VARCHAR(150) NOT NULL,
    business_registration_no    VARCHAR(100),
    verified_at                 TIMESTAMPTZ,
    verified_by                 UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at                  TIMESTAMPTZ
);

CREATE TRIGGER trg_vendors_updated_at
    BEFORE UPDATE ON vendors
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- admins
-- Purpose: administrator profile, 1:1 extension of `users`.
-- ---------------------------------------------------------------------
CREATE TABLE admins (
    user_id             UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    admin_level         admin_level_enum NOT NULL DEFAULT 'campus_admin',
    campus_id           UUID REFERENCES campuses (id) ON DELETE SET NULL, -- NULL => all campuses (super_admin)
    department          VARCHAR(100),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT ck_admins_super_admin_no_campus
        CHECK (admin_level <> 'super_admin' OR campus_id IS NULL)
);

CREATE INDEX ix_admins_campus_id ON admins (campus_id);

CREATE TRIGGER trg_admins_updated_at
    BEFORE UPDATE ON admins
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =====================================================================
-- SECTION 2: CAMPUS LOCATIONS
-- =====================================================================

-- ---------------------------------------------------------------------
-- locations
-- Purpose: flexible campus-position model. Deliberately NOT modeled
-- as "stalls belong to a block" — many stalls sit near, outside, or
-- opposite a block rather than inside one. `location_type` plus the
-- free-text `reference_label` capture that informal relationship
-- while `latitude`/`longitude` allow a precise pin once available.
-- ---------------------------------------------------------------------
CREATE TABLE locations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campus_id           UUID NOT NULL REFERENCES campuses (id) ON DELETE RESTRICT,
    location_type       location_type_enum NOT NULL,
    name                VARCHAR(150) NOT NULL,        -- e.g. "Block 34", "University Mall"
    reference_label      VARCHAR(150),                  -- e.g. "Near Block 34", "Opposite Block 55"
    description         TEXT,
    latitude             NUMERIC(9, 6),                 -- future precise geolocation
    longitude            NUMERIC(9, 6),
    floor                VARCHAR(20),
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_by           UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by           UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at           TIMESTAMPTZ,

    CONSTRAINT uq_locations_campus_name UNIQUE (campus_id, name),
    CONSTRAINT ck_locations_latitude CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CONSTRAINT ck_locations_longitude CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180)),
    CONSTRAINT ck_locations_lat_lng_pair CHECK (
        (latitude IS NULL AND longitude IS NULL) OR
        (latitude IS NOT NULL AND longitude IS NOT NULL)
    )
);

-- Location lookup (by campus) and nearby-stall support (by type +
-- coordinates). A precise radius search (PostGIS/earthdistance) is
-- deferred — see DATABASE_DECISIONS.md — but this composite index
-- supports the common "locations of type X on campus Y" query that
-- the Campus Navigator issues before ranking by distance in-app.
CREATE INDEX ix_locations_campus_id ON locations (campus_id);
CREATE INDEX ix_locations_campus_type ON locations (campus_id, location_type);
CREATE INDEX ix_locations_coordinates ON locations (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX ix_locations_deleted_at ON locations (deleted_at);

CREATE TRIGGER trg_locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- location_aliases
-- Purpose: normalized alternate names/spellings for a location (e.g.
-- "Lib" / "Library Block" / "Central Library" all resolve to one
-- `locations` row). Explicitly NOT a JSON/array column — one row per
-- alias — so each alias can be indexed and queried directly, and so
-- adding/removing an alias never requires reading-modifying-writing
-- a blob.
-- ---------------------------------------------------------------------
CREATE TABLE location_aliases (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id         UUID NOT NULL REFERENCES locations (id) ON DELETE CASCADE,
    alias               VARCHAR(150) NOT NULL,
    created_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_location_aliases_location_alias UNIQUE (location_id, alias)
);

CREATE INDEX ix_location_aliases_location_id ON location_aliases (location_id);
-- Natural-language / fuzzy lookup: "take me near the lib" -> matches alias "lib".
CREATE INDEX ix_location_aliases_alias_trgm ON location_aliases USING gin (alias gin_trgm_ops);

CREATE TRIGGER trg_location_aliases_updated_at
    BEFORE UPDATE ON location_aliases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =====================================================================
-- SECTION 3: FOOD STALLS & CATALOG
-- =====================================================================

-- ---------------------------------------------------------------------
-- stalls
-- Purpose: a vendor's sellable food outlet. References a `location`
-- rather than a block directly. `campus_id` is intentionally NOT
-- duplicated here (derived via stalls.location_id -> locations.campus_id)
-- to keep the schema in 3NF — see DATABASE_DECISIONS.md.
-- ---------------------------------------------------------------------
CREATE TABLE stalls (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id             UUID NOT NULL REFERENCES vendors (user_id) ON DELETE RESTRICT,
    location_id           UUID NOT NULL REFERENCES locations (id) ON DELETE RESTRICT,
    name                  VARCHAR(150) NOT NULL,
    slug                  VARCHAR(170) NOT NULL,
    description           TEXT,
    cuisine_type          VARCHAR(100),
    status                stall_status_enum NOT NULL DEFAULT 'pending_approval',
    is_accepting_orders   BOOLEAN NOT NULL DEFAULT FALSE,
    rating_avg            NUMERIC(3, 2) NOT NULL DEFAULT 0,
    rating_count          INTEGER NOT NULL DEFAULT 0,
    logo_url              VARCHAR(500),
    approved_at           TIMESTAMPTZ,
    approved_by           UUID REFERENCES users (id) ON DELETE SET NULL,
    created_by            UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by            UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at             TIMESTAMPTZ,

    CONSTRAINT uq_stalls_slug UNIQUE (slug),
    CONSTRAINT ck_stalls_rating_avg CHECK (rating_avg BETWEEN 0 AND 5),
    CONSTRAINT ck_stalls_rating_count CHECK (rating_count >= 0)
);

-- Vendor dashboard: "my stalls".
CREATE INDEX ix_stalls_vendor_id ON stalls (vendor_id);
-- Nearby stall lookup: join target from locations.
CREATE INDEX ix_stalls_location_id ON stalls (location_id);
-- Campus-aware search / browse: active stalls only.
CREATE INDEX ix_stalls_status ON stalls (status) WHERE deleted_at IS NULL;
CREATE INDEX ix_stalls_deleted_at ON stalls (deleted_at);
-- Natural-language search fallback on the stall's own name.
CREATE INDEX ix_stalls_name_trgm ON stalls USING gin (name gin_trgm_ops);

CREATE TRIGGER trg_stalls_updated_at
    BEFORE UPDATE ON stalls
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- stall_search_aliases
-- Purpose: normalized alternate names a student might use for a
-- stall in natural-language WhatsApp search (e.g. "Burger Shop" /
-- "Burger Point" / "Burger Stall" all resolve to one stall). One row
-- per alias, not a JSON/array column, for the same reasons as
-- location_aliases.
-- ---------------------------------------------------------------------
CREATE TABLE stall_search_aliases (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id            UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    alias               VARCHAR(150) NOT NULL,
    created_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_stall_search_aliases_stall_alias UNIQUE (stall_id, alias)
);

CREATE INDEX ix_stall_search_aliases_stall_id ON stall_search_aliases (stall_id);
-- Primary natural-language search index for stall discovery.
CREATE INDEX ix_stall_search_aliases_alias_trgm
    ON stall_search_aliases USING gin (alias gin_trgm_ops);

CREATE TRIGGER trg_stall_search_aliases_updated_at
    BEFORE UPDATE ON stall_search_aliases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- stall_operating_hours
-- Purpose: weekly recurring open/close schedule per stall. Split out
-- of `stalls` (rather than two columns on the stall row) because a
-- single opens_at/closes_at pair cannot represent different hours per
-- weekday — this normalization avoids update anomalies.
-- ---------------------------------------------------------------------
CREATE TABLE stall_operating_hours (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id            UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    day_of_week         SMALLINT NOT NULL,     -- 0 = Sunday ... 6 = Saturday
    opens_at            TIME,
    closes_at           TIME,
    is_closed           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_stall_hours_stall_day UNIQUE (stall_id, day_of_week),
    CONSTRAINT ck_stall_hours_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT ck_stall_hours_time_pair CHECK (
        is_closed = TRUE OR (opens_at IS NOT NULL AND closes_at IS NOT NULL AND opens_at < closes_at)
    )
);

CREATE INDEX ix_stall_hours_stall_id ON stall_operating_hours (stall_id);

CREATE TRIGGER trg_stall_hours_updated_at
    BEFORE UPDATE ON stall_operating_hours
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- menu_categories
-- Purpose: groups menu items within a stall (e.g. "Starters",
-- "Beverages") for display ordering and browsing.
-- ---------------------------------------------------------------------
CREATE TABLE menu_categories (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id            UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    name                VARCHAR(100) NOT NULL,
    display_order       INTEGER NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at           TIMESTAMPTZ,

    CONSTRAINT uq_menu_categories_stall_name UNIQUE (stall_id, name)
);

CREATE INDEX ix_menu_categories_stall_id ON menu_categories (stall_id);

CREATE TRIGGER trg_menu_categories_updated_at
    BEFORE UPDATE ON menu_categories
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- menu_items
-- Purpose: an individual sellable food/beverage item. Dietary
-- classification uses `food_type` (single enum) rather than separate
-- is_vegetarian/is_vegan booleans — see DATABASE_DECISIONS.md.
-- ---------------------------------------------------------------------
CREATE TABLE menu_items (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id                UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    category_id             UUID REFERENCES menu_categories (id) ON DELETE SET NULL,
    name                    VARCHAR(150) NOT NULL,
    description             TEXT,
    price                   NUMERIC(10, 2) NOT NULL,
    food_type               food_type_enum NOT NULL DEFAULT 'veg',
    spice_level             spice_level_enum,
    calories                INTEGER,
    image_url               VARCHAR(500),
    preparation_time_minutes SMALLINT,
    status                   menu_item_status_enum NOT NULL DEFAULT 'active',
    is_available             BOOLEAN NOT NULL DEFAULT TRUE,
    created_by                UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by                UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at                TIMESTAMPTZ,

    CONSTRAINT uq_menu_items_stall_name UNIQUE (stall_id, name),
    CONSTRAINT ck_menu_items_price CHECK (price >= 0),
    CONSTRAINT ck_menu_items_calories CHECK (calories IS NULL OR calories >= 0),
    CONSTRAINT ck_menu_items_prep_time CHECK (
        preparation_time_minutes IS NULL OR preparation_time_minutes >= 0
    )
);

CREATE INDEX ix_menu_items_stall_id ON menu_items (stall_id);
CREATE INDEX ix_menu_items_category_id ON menu_items (category_id);
CREATE INDEX ix_menu_items_status ON menu_items (status) WHERE deleted_at IS NULL;
CREATE INDEX ix_menu_items_food_type ON menu_items (food_type);
-- Natural-language / keyword fallback search on the item's own name.
CREATE INDEX ix_menu_items_name_trgm ON menu_items USING gin (name gin_trgm_ops);

CREATE TRIGGER trg_menu_items_updated_at
    BEFORE UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- menu_item_search_aliases
-- Purpose: normalized alternate names for a menu item (e.g. "French
-- Fries" / "Fries" / "Finger Chips" / "Potato Fries" all resolve to
-- one menu item). One row per alias, not a JSON/array column.
-- ---------------------------------------------------------------------
CREATE TABLE menu_item_search_aliases (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id        UUID NOT NULL REFERENCES menu_items (id) ON DELETE CASCADE,
    alias               VARCHAR(150) NOT NULL,
    created_by          UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_menu_item_search_aliases_item_alias UNIQUE (menu_item_id, alias)
);

CREATE INDEX ix_menu_item_search_aliases_item_id ON menu_item_search_aliases (menu_item_id);
-- Primary natural-language search index for menu item discovery.
CREATE INDEX ix_menu_item_search_aliases_alias_trgm
    ON menu_item_search_aliases USING gin (alias gin_trgm_ops);

CREATE TRIGGER trg_menu_item_search_aliases_updated_at
    BEFORE UPDATE ON menu_item_search_aliases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =====================================================================
-- SECTION 4: SEMANTIC SEARCH EMBEDDINGS (dedicated tables)
-- =====================================================================
-- Vector data is never mixed into menu/content tables. Each embeddable
-- entity gets its own 1:1 embeddings table, read/written exclusively
-- through the Repository layer — the AI layer never queries these (or
-- any table) with raw SQL.
-- =====================================================================

-- ---------------------------------------------------------------------
-- menu_item_embeddings
-- Purpose: vector representation of a menu item (name + description +
-- aliases) for Semantic Menu Search and Food Recommendation.
-- ---------------------------------------------------------------------
CREATE TABLE menu_item_embeddings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id        UUID NOT NULL REFERENCES menu_items (id) ON DELETE CASCADE,
    embedding           VECTOR(384) NOT NULL,   -- TODO: confirm dimension vs. chosen model
    model_version        VARCHAR(100) NOT NULL,
    generated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_menu_item_embeddings_item UNIQUE (menu_item_id)
);

-- Semantic search index.
CREATE INDEX ix_menu_item_embeddings_vector
    ON menu_item_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);


-- =====================================================================
-- SECTION 5: INVENTORY
-- =====================================================================

-- ---------------------------------------------------------------------
-- inventory
-- Purpose: current stock state for a menu item. 1:1 with menu_items
-- (an item either tracks inventory or doesn't; absence of a row means
-- "not stock-tracked" / always available). `status` is a derived,
-- vendor-dashboard-facing summary of the quantity columns.
-- ---------------------------------------------------------------------
CREATE TABLE inventory (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id          UUID NOT NULL REFERENCES menu_items (id) ON DELETE CASCADE,
    status                inventory_status_enum NOT NULL DEFAULT 'in_stock',
    quantity_available    INTEGER NOT NULL DEFAULT 0,
    quantity_reserved     INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold    INTEGER NOT NULL DEFAULT 5,
    last_restocked_at      TIMESTAMPTZ,
    updated_by               UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_inventory_menu_item UNIQUE (menu_item_id),
    CONSTRAINT ck_inventory_quantity_available CHECK (quantity_available >= 0),
    CONSTRAINT ck_inventory_quantity_reserved CHECK (quantity_reserved >= 0),
    CONSTRAINT ck_inventory_reserved_le_available CHECK (quantity_reserved <= quantity_available)
);

CREATE INDEX ix_inventory_menu_item_id ON inventory (menu_item_id);
-- Vendor dashboard: low-stock / out-of-stock alerts.
CREATE INDEX ix_inventory_status ON inventory (status);

CREATE TRIGGER trg_inventory_updated_at
    BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- inventory_logs
-- Purpose: immutable audit trail of every stock change. Append-only —
-- never updated or soft-deleted.
-- ---------------------------------------------------------------------
CREATE TABLE inventory_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id        UUID NOT NULL REFERENCES inventory (id) ON DELETE CASCADE,
    change_type         inventory_change_type_enum NOT NULL,
    quantity_delta       INTEGER NOT NULL,
    reason                TEXT,
    created_by             UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_inventory_logs_quantity_delta_nonzero CHECK (quantity_delta <> 0)
);

CREATE INDEX ix_inventory_logs_inventory_id ON inventory_logs (inventory_id);
CREATE INDEX ix_inventory_logs_created_at ON inventory_logs (created_at);


-- =====================================================================
-- SECTION 6: PICKUP SLOTS
-- =====================================================================

-- ---------------------------------------------------------------------
-- pickup_slots
-- Purpose: a bookable pickup window for a stall on a given date.
-- ---------------------------------------------------------------------
CREATE TABLE pickup_slots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id            UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    slot_date            DATE NOT NULL,
    start_time            TIME NOT NULL,
    end_time               TIME NOT NULL,
    capacity                INTEGER NOT NULL,
    booked_count             INTEGER NOT NULL DEFAULT 0,
    status                    pickup_slot_status_enum NOT NULL DEFAULT 'open',
    created_by                 UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_pickup_slots_stall_date_time UNIQUE (stall_id, slot_date, start_time, end_time),
    CONSTRAINT ck_pickup_slots_capacity CHECK (capacity > 0),
    CONSTRAINT ck_pickup_slots_booked_count CHECK (booked_count >= 0 AND booked_count <= capacity),
    CONSTRAINT ck_pickup_slots_time_order CHECK (start_time < end_time)
);

CREATE INDEX ix_pickup_slots_stall_date ON pickup_slots (stall_id, slot_date);
CREATE INDEX ix_pickup_slots_status ON pickup_slots (status);

CREATE TRIGGER trg_pickup_slots_updated_at
    BEFORE UPDATE ON pickup_slots
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =====================================================================
-- SECTION 7: ORDERS & PAYMENTS
-- =====================================================================

-- ---------------------------------------------------------------------
-- orders
-- Purpose: a student's food pre-booking against a single stall.
-- ---------------------------------------------------------------------
CREATE TABLE orders (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number           VARCHAR(30) NOT NULL,      -- human-readable, e.g. "CB-20260726-0001"
    student_id              UUID NOT NULL REFERENCES students (user_id) ON DELETE RESTRICT,
    stall_id                 UUID NOT NULL REFERENCES stalls (id) ON DELETE RESTRICT,
    pickup_slot_id             UUID REFERENCES pickup_slots (id) ON DELETE SET NULL,
    status                     order_status_enum NOT NULL DEFAULT 'pending_payment',
    placed_via                  order_source_enum NOT NULL DEFAULT 'whatsapp',
    subtotal_amount               NUMERIC(10, 2) NOT NULL,
    total_amount                   NUMERIC(10, 2) NOT NULL,
    currency                         CHAR(3) NOT NULL DEFAULT 'INR',
    special_instructions               TEXT,
    cancelled_at                        TIMESTAMPTZ,
    cancelled_reason                     TEXT,
    created_at                            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                             TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_orders_order_number UNIQUE (order_number),
    CONSTRAINT ck_orders_subtotal_amount CHECK (subtotal_amount >= 0),
    CONSTRAINT ck_orders_total_amount CHECK (total_amount >= 0),
    CONSTRAINT ck_orders_cancelled_fields CHECK (
        (status <> 'cancelled') OR (cancelled_at IS NOT NULL)
    )
);

-- Order history (student-facing).
CREATE INDEX ix_orders_student_id ON orders (student_id, created_at);
-- Vendor dashboard (stall-facing order queue).
CREATE INDEX ix_orders_stall_status ON orders (stall_id, status);
CREATE INDEX ix_orders_status ON orders (status);
CREATE INDEX ix_orders_created_at ON orders (created_at);
CREATE INDEX ix_orders_pickup_slot_id ON orders (pickup_slot_id);

CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- order_items
-- Purpose: line items of an order. `unit_price` is a PRICE SNAPSHOT
-- at order time — intentionally duplicates menu_items.price so later
-- price changes never rewrite order history (documented denormalization,
-- see DATABASE_DECISIONS.md).
-- ---------------------------------------------------------------------
CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id             UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    menu_item_id          UUID NOT NULL REFERENCES menu_items (id) ON DELETE RESTRICT,
    item_name_snapshot      VARCHAR(150) NOT NULL,
    quantity                  INTEGER NOT NULL,
    unit_price                  NUMERIC(10, 2) NOT NULL,
    subtotal                      NUMERIC(10, 2) NOT NULL,
    special_instructions            TEXT,
    created_at                        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_order_items_order_menu_item UNIQUE (order_id, menu_item_id),
    CONSTRAINT ck_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT ck_order_items_unit_price CHECK (unit_price >= 0),
    CONSTRAINT ck_order_items_subtotal CHECK (subtotal >= 0)
);

CREATE INDEX ix_order_items_order_id ON order_items (order_id);
CREATE INDEX ix_order_items_menu_item_id ON order_items (menu_item_id);


-- ---------------------------------------------------------------------
-- order_status_history
-- Purpose: append-only audit trail of every order status transition.
-- Backs order tracking updates sent over WhatsApp.
-- ---------------------------------------------------------------------
CREATE TABLE order_status_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id             UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    status                 order_status_enum NOT NULL,
    changed_by               UUID REFERENCES users (id) ON DELETE SET NULL,
    notes                      TEXT,
    changed_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_order_status_history_order_id ON order_status_history (order_id);
CREATE INDEX ix_order_status_history_changed_at ON order_status_history (changed_at);


-- ---------------------------------------------------------------------
-- payments
-- Purpose: payment record for an order (1:1). See DATABASE_DECISIONS.md
-- for the deferred 1:1-vs-1:N retry-semantics decision.
-- ---------------------------------------------------------------------
CREATE TABLE payments (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id                    UUID NOT NULL REFERENCES orders (id) ON DELETE RESTRICT,
    payment_method                 payment_method_enum NOT NULL,
    amount                           NUMERIC(10, 2) NOT NULL,
    currency                           CHAR(3) NOT NULL DEFAULT 'INR',
    status                               payment_status_enum NOT NULL DEFAULT 'initiated',
    provider                              VARCHAR(50),
    provider_transaction_id                 VARCHAR(150),
    qr_code_reference                         VARCHAR(255),
    paid_at                                     TIMESTAMPTZ,
    created_at                                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                                     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_payments_order_id UNIQUE (order_id),
    CONSTRAINT uq_payments_provider_transaction_id UNIQUE (provider_transaction_id),
    CONSTRAINT ck_payments_amount CHECK (amount >= 0)
);

CREATE INDEX ix_payments_status ON payments (status);
CREATE INDEX ix_payments_order_id ON payments (order_id);

CREATE TRIGGER trg_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- payment_refunds
-- Purpose: refund records against a payment. 1:N — a payment may be
-- partially refunded more than once.
-- ---------------------------------------------------------------------
CREATE TABLE payment_refunds (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id           UUID NOT NULL REFERENCES payments (id) ON DELETE RESTRICT,
    amount                 NUMERIC(10, 2) NOT NULL,
    reason                    TEXT,
    status                     refund_status_enum NOT NULL DEFAULT 'initiated',
    processed_at                 TIMESTAMPTZ,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_payment_refunds_amount CHECK (amount > 0)
);

CREATE INDEX ix_payment_refunds_payment_id ON payment_refunds (payment_id);

CREATE TRIGGER trg_payment_refunds_updated_at
    BEFORE UPDATE ON payment_refunds
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =====================================================================
-- SECTION 8: KITCHEN WORKFLOW & QUEUE ENGINE
-- =====================================================================

-- ---------------------------------------------------------------------
-- kitchen_tickets
-- Purpose: kitchen-side execution state for an order, separate from
-- the customer-facing `orders.status`. See DATABASE_DECISIONS.md.
-- ---------------------------------------------------------------------
CREATE TABLE kitchen_tickets (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id                  UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    stall_id                    UUID NOT NULL REFERENCES stalls (id) ON DELETE RESTRICT,
    status                        kitchen_status_enum NOT NULL DEFAULT 'queued',
    priority                        SMALLINT NOT NULL DEFAULT 0,
    assigned_to                       UUID REFERENCES users (id) ON DELETE SET NULL,
    estimated_ready_at                  TIMESTAMPTZ,
    started_at                            TIMESTAMPTZ,
    completed_at                            TIMESTAMPTZ,
    created_at                                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                                  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_kitchen_tickets_order_id UNIQUE (order_id)
);

-- Kitchen/vendor dashboard: active tickets per stall by status.
CREATE INDEX ix_kitchen_tickets_stall_status ON kitchen_tickets (stall_id, status);

CREATE TRIGGER trg_kitchen_tickets_updated_at
    BEFORE UPDATE ON kitchen_tickets
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- stall_queues
-- Purpose: current, frequently-updated queue snapshot per stall, used
-- by Queue Optimization / ETA Prediction for low-latency reads. 1:1
-- with stalls.
-- ---------------------------------------------------------------------
CREATE TABLE stall_queues (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id                          UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    current_queue_length                INTEGER NOT NULL DEFAULT 0,
    average_prep_time_seconds              INTEGER,
    last_updated_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_stall_queues_stall_id UNIQUE (stall_id),
    CONSTRAINT ck_stall_queues_length CHECK (current_queue_length >= 0)
);

-- Queue lookup by stall (already covered by the unique constraint's
-- implicit index; explicit index kept for read clarity/consistency
-- with the other "queue" indexes below).
CREATE INDEX ix_stall_queues_stall_id ON stall_queues (stall_id);


-- ---------------------------------------------------------------------
-- queue_events
-- Purpose: append-only event log feeding queue-length history and ETA
-- model training/evaluation.
-- ---------------------------------------------------------------------
CREATE TABLE queue_events (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id                  UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    order_id                    UUID REFERENCES orders (id) ON DELETE SET NULL,
    event_type                    queue_event_type_enum NOT NULL,
    queue_length_at_event            INTEGER NOT NULL,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_queue_events_length CHECK (queue_length_at_event >= 0)
);

CREATE INDEX ix_queue_events_stall_id ON queue_events (stall_id, created_at);


-- ---------------------------------------------------------------------
-- eta_predictions
-- Purpose: stores each ETA prediction alongside the eventual actual
-- ready time, enabling offline evaluation/retraining of the
-- prediction model.
-- ---------------------------------------------------------------------
CREATE TABLE eta_predictions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id                  UUID NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    predicted_ready_at           TIMESTAMPTZ NOT NULL,
    predicted_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_version                     VARCHAR(100) NOT NULL,
    actual_ready_at                     TIMESTAMPTZ,
    created_at                            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_eta_predictions_order_id UNIQUE (order_id)
);


-- =====================================================================
-- SECTION 9: CONVERSATION SESSIONS (WhatsApp AI agent state)
-- =====================================================================

-- ---------------------------------------------------------------------
-- conversation_sessions
-- Purpose: durable WhatsApp conversation state per user, powering the
-- Intent Engine and LLM tool-calling. Holds coarse state (`state`),
-- the in-progress selection (stall / pickup slot / cart), free-form
-- slot-filling context for the AI layer, and an expiry so stale
-- sessions can be reset. Exactly one *active* session per user is
-- enforced via a partial unique index on `is_active`.
-- ---------------------------------------------------------------------
CREATE TABLE conversation_sessions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    campus_id                    UUID REFERENCES campuses (id) ON DELETE SET NULL,
    state                          conversation_state_enum NOT NULL DEFAULT 'idle',
    current_intent                    VARCHAR(100),
    selected_stall_id                    UUID REFERENCES stalls (id) ON DELETE SET NULL,
    selected_pickup_slot_id                 UUID REFERENCES pickup_slots (id) ON DELETE SET NULL,
    cart_items                                 JSONB NOT NULL DEFAULT '[]'::JSONB,
    draft_order_id                                UUID REFERENCES orders (id) ON DELETE SET NULL,
    context                                          JSONB NOT NULL DEFAULT '{}'::JSONB,
    is_active                                           BOOLEAN NOT NULL DEFAULT TRUE,
    last_interaction_at                                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at                                                TIMESTAMPTZ NOT NULL,
    created_at                                                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                                                    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_conversation_sessions_cart_items_is_array
        CHECK (jsonb_typeof(cart_items) = 'array'),
    CONSTRAINT ck_conversation_sessions_context_is_object
        CHECK (jsonb_typeof(context) = 'object')
);

-- Enforce a single active session per user (see purpose note above).
CREATE UNIQUE INDEX uq_conversation_sessions_active_user
    ON conversation_sessions (user_id) WHERE is_active = TRUE;

CREATE INDEX ix_conversation_sessions_user_id ON conversation_sessions (user_id);
-- Background expiry sweep.
CREATE INDEX ix_conversation_sessions_expires_at ON conversation_sessions (expires_at)
    WHERE is_active = TRUE;
CREATE INDEX ix_conversation_sessions_state ON conversation_sessions (state);

CREATE TRIGGER trg_conversation_sessions_updated_at
    BEFORE UPDATE ON conversation_sessions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- TODO(milestone: AI / conversation layer): once the Intent Engine's
-- exact slot-filling schema is finalized, consider a CHECK on
-- `context` keys or a companion typed table if free-form JSONB proves
-- too loose for a given intent. Left flexible deliberately for now.


-- =====================================================================
-- SECTION 10: NOTIFICATIONS
-- =====================================================================

-- ---------------------------------------------------------------------
-- notification_templates
-- Purpose: reusable message templates (order confirmed, ready for
-- pickup, etc.) referenced by outbound notifications.
-- ---------------------------------------------------------------------
CREATE TABLE notification_templates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                 VARCHAR(100) NOT NULL,
    channel                notification_channel_enum NOT NULL,
    title                     VARCHAR(150),
    body_template               TEXT NOT NULL,
    is_active                     BOOLEAN NOT NULL DEFAULT TRUE,
    created_by                      UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by                        UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_notification_templates_code UNIQUE (code)
);

CREATE TRIGGER trg_notification_templates_updated_at
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- notifications
-- Purpose: every outbound message sent to a user, primarily over
-- WhatsApp, with delivery status tracking.
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    order_id                     UUID REFERENCES orders (id) ON DELETE SET NULL,
    template_id                    UUID REFERENCES notification_templates (id) ON DELETE SET NULL,
    channel                          notification_channel_enum NOT NULL,
    recipient                          VARCHAR(255) NOT NULL,
    subject                              VARCHAR(150),
    body                                   TEXT NOT NULL,
    status                                   notification_status_enum NOT NULL DEFAULT 'pending',
    provider_message_id                        VARCHAR(150),
    error_message                                TEXT,
    sent_at                                        TIMESTAMPTZ,
    delivered_at                                     TIMESTAMPTZ,
    read_at                                            TIMESTAMPTZ,
    created_at                                           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id, created_at);
CREATE INDEX ix_notifications_order_id ON notifications (order_id);
CREATE INDEX ix_notifications_status ON notifications (status);


-- =====================================================================
-- SECTION 11: RECOMMENDATIONS & SEARCH ANALYTICS
-- =====================================================================

-- ---------------------------------------------------------------------
-- recommendation_events
-- Purpose: logs every recommendation impression shown to a student,
-- and whether it converted — the feedback loop for Food Recommendation.
-- ---------------------------------------------------------------------
CREATE TABLE recommendation_events (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id                  UUID NOT NULL REFERENCES students (user_id) ON DELETE CASCADE,
    menu_item_id                   UUID REFERENCES menu_items (id) ON DELETE SET NULL,
    stall_id                          UUID REFERENCES stalls (id) ON DELETE SET NULL,
    recommendation_type                  recommendation_type_enum NOT NULL,
    score                                    NUMERIC(5, 4),
    context                                    JSONB,
    shown_at                                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    clicked                                        BOOLEAN NOT NULL DEFAULT FALSE,
    clicked_at                                       TIMESTAMPTZ,
    converted_order_id                                 UUID REFERENCES orders (id) ON DELETE SET NULL,

    CONSTRAINT ck_recommendation_events_score CHECK (score IS NULL OR (score BETWEEN 0 AND 1)),
    CONSTRAINT ck_recommendation_events_target CHECK (
        menu_item_id IS NOT NULL OR stall_id IS NOT NULL
    )
);

CREATE INDEX ix_recommendation_events_student_id ON recommendation_events (student_id, shown_at);


-- ---------------------------------------------------------------------
-- search_queries
-- Purpose: logs every search issued (natural language, semantic, or
-- keyword) for Campus-aware Search analytics and future ranking
-- improvements.
-- ---------------------------------------------------------------------
CREATE TABLE search_queries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID REFERENCES users (id) ON DELETE SET NULL,
    campus_id               UUID REFERENCES campuses (id) ON DELETE SET NULL,
    query_text                 TEXT NOT NULL,
    query_type                    search_query_type_enum NOT NULL,
    results_count                    INTEGER NOT NULL DEFAULT 0,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_search_queries_results_count CHECK (results_count >= 0)
);

-- Analytics: search volume/effectiveness by campus over time.
CREATE INDEX ix_search_queries_campus_created ON search_queries (campus_id, created_at);
CREATE INDEX ix_search_queries_created_at ON search_queries (created_at);


-- ---------------------------------------------------------------------
-- faq_documents
-- Purpose: knowledge-base source documents for the RAG-based FAQ
-- feature. Vector data lives in `faq_document_embeddings`, not here.
-- ---------------------------------------------------------------------
CREATE TABLE faq_documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campus_id             UUID REFERENCES campuses (id) ON DELETE CASCADE,  -- NULL => platform-wide
    title                    VARCHAR(255) NOT NULL,
    content                     TEXT NOT NULL,
    source_url                     VARCHAR(500),
    is_active                        BOOLEAN NOT NULL DEFAULT TRUE,
    created_by                         UUID REFERENCES users (id) ON DELETE SET NULL,
    updated_by                           UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at                             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                               TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at                                 TIMESTAMPTZ
);

CREATE INDEX ix_faq_documents_campus_id ON faq_documents (campus_id);

CREATE TRIGGER trg_faq_documents_updated_at
    BEFORE UPDATE ON faq_documents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ---------------------------------------------------------------------
-- faq_document_embeddings
-- Purpose: vector representation of a FAQ document for RAG retrieval.
-- Split from `faq_documents` for the same reason as
-- `menu_item_embeddings` — vector data is never mixed into content
-- tables.
-- ---------------------------------------------------------------------
CREATE TABLE faq_document_embeddings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_document_id     UUID NOT NULL REFERENCES faq_documents (id) ON DELETE CASCADE,
    embedding           VECTOR(384) NOT NULL,   -- TODO: confirm dimension vs. chosen model
    model_version        VARCHAR(100) NOT NULL,
    generated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_faq_document_embeddings_document UNIQUE (faq_document_id)
);

-- Semantic search index for RAG retrieval.
CREATE INDEX ix_faq_document_embeddings_vector
    ON faq_document_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);


-- =====================================================================
-- SECTION 12: ANALYTICS
-- =====================================================================

-- ---------------------------------------------------------------------
-- daily_stall_analytics
-- Purpose: pre-aggregated per-stall, per-day rollup for vendor/admin
-- analytics dashboards, avoiding expensive on-demand aggregation over
-- `orders` at read time.
-- ---------------------------------------------------------------------
CREATE TABLE daily_stall_analytics (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stall_id                    UUID NOT NULL REFERENCES stalls (id) ON DELETE CASCADE,
    analytics_date                 DATE NOT NULL,
    total_orders                      INTEGER NOT NULL DEFAULT 0,
    total_revenue                        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cancelled_orders                        INTEGER NOT NULL DEFAULT 0,
    average_prep_time_seconds                  INTEGER,
    created_at                                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                                      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_daily_stall_analytics_stall_date UNIQUE (stall_id, analytics_date),
    CONSTRAINT ck_daily_stall_analytics_totals CHECK (
        total_orders >= 0 AND total_revenue >= 0 AND cancelled_orders >= 0
    )
);

-- Analytics: per-stall trend queries and cross-stall daily rollup scans.
CREATE INDEX ix_daily_stall_analytics_stall_date ON daily_stall_analytics (stall_id, analytics_date);
CREATE INDEX ix_daily_stall_analytics_date ON daily_stall_analytics (analytics_date);

CREATE TRIGGER trg_daily_stall_analytics_updated_at
    BEFORE UPDATE ON daily_stall_analytics
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =====================================================================
-- END OF SCHEMA — Milestone 2 (Revised / FINAL)
-- =====================================================================
