-- =====================================================================
-- CampusBite AI — Database ENUM Types
-- Milestone 2 (Revised / FINAL): Database Architecture
--
-- Load this file BEFORE schema.sql.
-- Naming convention: <domain>_<concept>_enum
--
-- This revision supersedes the prior enums.sql. Two enums were
-- renamed for naming-convention consistency with this milestone's
-- explicit enum list, and two are new. See DATABASE_DECISIONS.md
-- §"Revision notes" for the full diff and rationale.
--   - slot_status_enum          -> pickup_slot_status_enum (renamed)
--   - kitchen_ticket_status_enum -> kitchen_status_enum     (renamed)
--   - inventory_status_enum      (new)
--   - conversation_state_enum    (new)
--   - food_type_enum             (new — replaces is_vegetarian/is_vegan booleans)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Identity
-- ---------------------------------------------------------------------

-- Top-level role of a `users` row. Drives which subtype table
-- (students / vendors / admins) has a matching row.
CREATE TYPE user_role_enum AS ENUM (
    'student',
    'vendor',
    'admin'
);

-- Administrative privilege tier. Only meaningful for rows in `admins`.
CREATE TYPE admin_level_enum AS ENUM (
    'super_admin',      -- full platform access, all campuses
    'campus_admin',      -- scoped to one campus
    'support_staff'      -- read-mostly, limited operational actions
);

-- ---------------------------------------------------------------------
-- Campus & Location
-- ---------------------------------------------------------------------

-- Classifies how a `locations` row should be interpreted by
-- Campus-aware Search / Campus Food Navigator. Stalls are frequently
-- located NEAR a landmark rather than inside a formal building, so
-- this type deliberately supports informal, relative positioning.
CREATE TYPE location_type_enum AS ENUM (
    'block',             -- a formal, numbered campus block/building
    'nearby_block',       -- informally described as "near Block N"
    'building',            -- a named building that is not a numbered block
    'landmark',             -- a named campus landmark (e.g. Library, Auditorium)
    'outdoor_area',          -- open-air area (courtyard, ground, parking lot)
    'open_space'              -- unstructured open space with no formal name
);

-- ---------------------------------------------------------------------
-- Stalls & Catalog
-- ---------------------------------------------------------------------

CREATE TYPE stall_status_enum AS ENUM (
    'pending_approval',   -- created by vendor, awaiting admin approval
    'active',              -- visible and orderable
    'inactive',            -- hidden by vendor/admin, not deleted
    'suspended',           -- disabled by admin (policy violation, etc.)
    'closed_temporarily'   -- vendor-declared temporary closure (holiday, etc.)
);

CREATE TYPE menu_item_status_enum AS ENUM (
    'active',
    'inactive',
    'out_of_stock'
);

-- Dietary classification of a menu item. Replaces the earlier
-- is_vegetarian/is_vegan boolean pair with a single, exhaustive,
-- mutually-exclusive classification — see DATABASE_DECISIONS.md.
CREATE TYPE food_type_enum AS ENUM (
    'veg',
    'non_veg',
    'egg',
    'vegan'
);

CREATE TYPE spice_level_enum AS ENUM (
    'none',
    'mild',
    'medium',
    'hot',
    'extra_hot'
);

-- ---------------------------------------------------------------------
-- Inventory
-- ---------------------------------------------------------------------

CREATE TYPE inventory_change_type_enum AS ENUM (
    'restock',
    'sale',
    'cancellation',
    'adjustment',          -- manual correction by vendor/admin
    'wastage'
);

-- Derived/operational status of an inventory row, surfaced directly
-- to vendors on the dashboard without them having to read raw
-- quantities. Kept in sync with quantity_available by the service
-- layer (a future milestone), not by a DB trigger — see decisions doc.
CREATE TYPE inventory_status_enum AS ENUM (
    'in_stock',
    'low_stock',
    'out_of_stock',
    'discontinued'
);

-- ---------------------------------------------------------------------
-- Orders & Payments
-- ---------------------------------------------------------------------

CREATE TYPE order_status_enum AS ENUM (
    'pending_payment',
    'confirmed',
    'preparing',
    'ready_for_pickup',
    'completed',
    'cancelled',
    'refunded'
);

CREATE TYPE order_source_enum AS ENUM (
    'whatsapp',
    'dashboard',
    'mobile_app',
    'kiosk'
);

CREATE TYPE payment_method_enum AS ENUM (
    'upi_qr',
    'card',
    'wallet',
    'cash'
);

CREATE TYPE payment_status_enum AS ENUM (
    'initiated',
    'pending',
    'success',
    'failed',
    'refunded',
    'partially_refunded'
);

CREATE TYPE refund_status_enum AS ENUM (
    'initiated',
    'processed',
    'failed'
);

-- ---------------------------------------------------------------------
-- Pickup Slots
-- ---------------------------------------------------------------------

CREATE TYPE pickup_slot_status_enum AS ENUM (
    'open',
    'closed',
    'full'
);

-- ---------------------------------------------------------------------
-- Kitchen Workflow & Queue Engine
-- ---------------------------------------------------------------------

-- Kitchen-facing status, distinct from the customer-facing
-- `order_status_enum`. See DATABASE_DECISIONS.md for the rationale.
CREATE TYPE kitchen_status_enum AS ENUM (
    'queued',
    'in_progress',
    'ready',
    'served',
    'cancelled'
);

CREATE TYPE queue_event_type_enum AS ENUM (
    'order_queued',
    'order_started',
    'order_completed',
    'order_cancelled'
);

-- ---------------------------------------------------------------------
-- Notifications
-- ---------------------------------------------------------------------

CREATE TYPE notification_channel_enum AS ENUM (
    'whatsapp',
    'sms',
    'email',
    'push'
);

CREATE TYPE notification_status_enum AS ENUM (
    'pending',
    'sent',
    'delivered',
    'failed',
    'read'
);

-- ---------------------------------------------------------------------
-- Conversation Sessions (WhatsApp AI agent state machine)
-- ---------------------------------------------------------------------

-- Coarse-grained state of a student's WhatsApp conversation, driving
-- what the Intent Engine expects next. Fine-grained slot data lives
-- in conversation_sessions.context (JSONB), not in this enum — this
-- enum is deliberately small and stable so it rarely needs a migration.
CREATE TYPE conversation_state_enum AS ENUM (
    'idle',
    'browsing_stalls',
    'browsing_menu',
    'building_order',
    'awaiting_pickup_slot',
    'awaiting_payment',
    'order_confirmed',
    'faq',
    'escalated_to_human',
    'expired'
);

-- ---------------------------------------------------------------------
-- AI: Recommendations & Search
-- ---------------------------------------------------------------------

CREATE TYPE recommendation_type_enum AS ENUM (
    'personalized',
    'trending',
    'similar_item',
    'campus_popular'
);

CREATE TYPE search_query_type_enum AS ENUM (
    'natural_language',
    'semantic',
    'keyword'
);
