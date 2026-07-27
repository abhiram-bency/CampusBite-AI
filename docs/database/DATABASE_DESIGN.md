# DATABASE_DESIGN.md — CampusBite AI

**Milestone 2 (Revised / FINAL): Database Architecture**
This design is considered **frozen** once accepted — it is the single
source of truth for all subsequent implementation milestones (per
Project Rule #6). Companion files: `enums.sql`, `schema.sql`,
`ER_DIAGRAM.md`, `DATABASE_DECISIONS.md`.

Conventions used throughout:
- Primary keys: `UUID DEFAULT gen_random_uuid()`, matching the completed `app/database/base.py` / `mixins.py` infrastructure.
- Audit columns: `created_at`, `updated_at` (auto-maintained via trigger) on every mutable table, plus `created_by` / `updated_by` (FK → `users.id`) on tables a human vendor/admin directly edits.
- Soft delete (`deleted_at`, nullable) applied only to master/reference tables — never to transactional or append-only log tables (see `DATABASE_DECISIONS.md` §"Soft Delete Policy").
- Normalized alias/search tables (`location_aliases`, `stall_search_aliases`, `menu_item_search_aliases`) — never JSON/array columns.

---

## Section 1 — Identity

### `users`
**Purpose:** Root identity for every actor (student, vendor, admin).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| role | user_role_enum | No | — | student / vendor / admin |
| phone_number | VARCHAR(20) | No | — | WhatsApp identity |
| email | VARCHAR(255) | Yes | — | optional, dashboard login |
| full_name | VARCHAR(150) | No | — | |
| password_hash | VARCHAR(255) | Yes | — | NULL for WhatsApp-only students |
| is_active | BOOLEAN | No | `TRUE` | |
| phone_verified_at | TIMESTAMPTZ | Yes | — | |
| last_login_at | TIMESTAMPTZ | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **Unique:** `phone_number`; `email`
- **Check:** `phone_number ~ '^\+?[0-9]{8,15}$'`
- **Indexes:** `role` (partial, active rows); `deleted_at`
- **Relationships:** 1:1 → `students`, `vendors`, `admins`; 1:N → `notifications`, `conversation_sessions`

### `campuses`
**Purpose:** Tenant root for multi-campus support.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| name | VARCHAR(150) | No | — | |
| code | VARCHAR(20) | No | — | short code, e.g. "MAIN" |
| address | TEXT | Yes | — | |
| timezone | VARCHAR(50) | No | `'Asia/Kolkata'` | |
| is_active | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **Unique:** `code`
- **Indexes:** `deleted_at`; trigram GIN on `name` (campus search)
- **Relationships:** 1:N → `locations`, `students`, `admins`, `conversation_sessions`, `search_queries`, `faq_documents`

### `students`
**Purpose:** Student profile; 1:1 extension of `users`. `registration_number` is the WhatsApp login credential.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| user_id | UUID | No | — | PK, FK → users.id |
| campus_id | UUID | No | — | FK → campuses.id |
| registration_number | VARCHAR(50) | No | — | |
| department | VARCHAR(100) | Yes | — | |
| year_of_study | SMALLINT | Yes | — | 1–8 |
| hostel_or_block | VARCHAR(100) | Yes | — | free text |
| dietary_preference | food_type_enum | Yes | — | reuses food_type_enum |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `user_id` · **FK:** `user_id → users.id` (CASCADE); `campus_id → campuses.id` (RESTRICT)
- **Unique:** `registration_number` · **Check:** `year_of_study BETWEEN 1 AND 8`
- **Indexes:** `campus_id`
- **Relationships:** 1:N → `orders`, `recommendation_events`

### `vendors`
**Purpose:** Vendor (stall owner) profile; 1:1 extension of `users`.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| user_id | UUID | No | — | PK, FK → users.id |
| business_name | VARCHAR(150) | No | — | |
| business_registration_no | VARCHAR(100) | Yes | — | |
| verified_at | TIMESTAMPTZ | Yes | — | |
| verified_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `user_id` · **FK:** `user_id → users.id` (CASCADE); `verified_by → users.id` (SET NULL)
- **Relationships:** 1:N → `stalls`

### `admins`
**Purpose:** Administrator profile; 1:1 extension of `users`.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| user_id | UUID | No | — | PK, FK → users.id |
| admin_level | admin_level_enum | No | `'campus_admin'` | |
| campus_id | UUID | Yes | — | NULL = all campuses |
| department | VARCHAR(100) | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `user_id` · **FK:** `user_id → users.id` (CASCADE); `campus_id → campuses.id` (SET NULL)
- **Check:** `admin_level <> 'super_admin' OR campus_id IS NULL`
- **Indexes:** `campus_id`

---

## Section 2 — Campus Locations

### `locations`
**Purpose:** Flexible campus-position model (Block / Nearby Block / Building / Landmark / Outdoor Area / Open Space) — stalls are never assumed to sit inside a block.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| campus_id | UUID | No | — | FK → campuses.id |
| location_type | location_type_enum | No | — | |
| name | VARCHAR(150) | No | — | e.g. "Block 34", "University Mall" |
| reference_label | VARCHAR(150) | Yes | — | e.g. "Near Block 34" |
| description | TEXT | Yes | — | |
| latitude | NUMERIC(9,6) | Yes | — | future precise geolocation |
| longitude | NUMERIC(9,6) | Yes | — | |
| floor | VARCHAR(20) | Yes | — | |
| is_active | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **FK:** `campus_id → campuses.id` (RESTRICT); `created_by`/`updated_by → users.id` (SET NULL)
- **Unique:** `(campus_id, name)`
- **Check:** lat/lng range checks; lat/lng must both be set or both NULL
- **Indexes:** `campus_id`; `(campus_id, location_type)` (nearby-lookup pre-filter); `(latitude, longitude)` partial (geolocated rows only); `deleted_at`
- **Relationships:** 1:N → `location_aliases`, `stalls`

### `location_aliases`
**Purpose:** Normalized alternate names/spellings for a location (e.g. "Lib" / "Library Block" / "Central Library"). One row per alias.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| location_id | UUID | No | — | FK → locations.id |
| alias | VARCHAR(150) | No | — | |
| created_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `location_id → locations.id` (CASCADE); `created_by → users.id` (SET NULL)
- **Unique:** `(location_id, alias)`
- **Indexes:** `location_id`; trigram GIN on `alias` (natural-language lookup)
- **Soft delete:** not applied — an alias is either present or removed outright; there is no meaningful "retired alias" state worth preserving.

---

## Section 3 — Stalls & Catalog

### `stalls`
**Purpose:** A vendor's sellable food outlet, positioned via `location_id`.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| vendor_id | UUID | No | — | FK → vendors.user_id |
| location_id | UUID | No | — | FK → locations.id |
| name | VARCHAR(150) | No | — | |
| slug | VARCHAR(170) | No | — | |
| description | TEXT | Yes | — | |
| cuisine_type | VARCHAR(100) | Yes | — | |
| status | stall_status_enum | No | `'pending_approval'` | |
| is_accepting_orders | BOOLEAN | No | `FALSE` | |
| rating_avg | NUMERIC(3,2) | No | `0` | 0–5 |
| rating_count | INTEGER | No | `0` | |
| logo_url | VARCHAR(500) | Yes | — | |
| approved_at | TIMESTAMPTZ | Yes | — | |
| approved_by | UUID | Yes | — | FK → users.id |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **FK:** `vendor_id → vendors.user_id` (RESTRICT); `location_id → locations.id` (RESTRICT); `approved_by`/`created_by`/`updated_by → users.id` (SET NULL)
- **Unique:** `slug`
- **Check:** `rating_avg BETWEEN 0 AND 5`; `rating_count >= 0`
- **Indexes:** `vendor_id` (vendor dashboard); `location_id` (nearby-stall lookup); `status` partial (browse/search); `deleted_at`; trigram GIN on `name` (NL search fallback)
- **Relationships:** 1:N → `stall_search_aliases`, `stall_operating_hours`, `menu_categories`, `menu_items`, `pickup_slots`, `orders`, `kitchen_tickets`, `queue_events`; 1:1 → `stall_queues`
- **Note:** no `campus_id` column — derived via `location_id` (documented in decisions doc).

### `stall_search_aliases`
**Purpose:** Normalized alternate names a student might use in natural-language search (e.g. "Burger Shop" / "Burger Point" / "Burger Stall" → one stall).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| alias | VARCHAR(150) | No | — | |
| created_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE); `created_by → users.id` (SET NULL)
- **Unique:** `(stall_id, alias)`
- **Indexes:** `stall_id`; trigram GIN on `alias` — **primary index for stall natural-language search**

### `stall_operating_hours`
**Purpose:** Weekly recurring open/close schedule per stall (one row per weekday).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| day_of_week | SMALLINT | No | — | 0=Sunday … 6=Saturday |
| opens_at / closes_at | TIME | Yes | — | required unless `is_closed` |
| is_closed | BOOLEAN | No | `FALSE` | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE)
- **Unique:** `(stall_id, day_of_week)`
- **Check:** `day_of_week BETWEEN 0 AND 6`; time ordering when not closed
- **Indexes:** `stall_id`

### `menu_categories`
**Purpose:** Groups menu items within a stall for browsing/display order.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| name | VARCHAR(100) | No | — | |
| display_order | INTEGER | No | `0` | |
| is_active | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE)
- **Unique:** `(stall_id, name)` · **Indexes:** `stall_id`
- **Relationships:** 1:N → `menu_items`

### `menu_items`
**Purpose:** An individual sellable food/beverage item. Dietary classification uses a single `food_type` enum.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| category_id | UUID | Yes | — | FK → menu_categories.id |
| name | VARCHAR(150) | No | — | |
| description | TEXT | Yes | — | |
| price | NUMERIC(10,2) | No | — | |
| food_type | food_type_enum | No | `'veg'` | veg / non_veg / egg / vegan |
| spice_level | spice_level_enum | Yes | — | |
| calories | INTEGER | Yes | — | |
| image_url | VARCHAR(500) | Yes | — | |
| preparation_time_minutes | SMALLINT | Yes | — | |
| status | menu_item_status_enum | No | `'active'` | |
| is_available | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE); `category_id → menu_categories.id` (SET NULL)
- **Unique:** `(stall_id, name)`
- **Check:** `price >= 0`; `calories >= 0` if set; `preparation_time_minutes >= 0` if set
- **Indexes:** `stall_id`; `category_id`; `status` partial; `food_type`; trigram GIN on `name`
- **Relationships:** 1:N → `menu_item_search_aliases`, `order_items`, `recommendation_events`; 1:1 → `menu_item_embeddings`, `inventory`

### `menu_item_search_aliases`
**Purpose:** Normalized alternate names for a menu item (e.g. "French Fries" / "Fries" / "Finger Chips" / "Potato Fries" → one item).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| menu_item_id | UUID | No | — | FK → menu_items.id |
| alias | VARCHAR(150) | No | — | |
| created_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `menu_item_id → menu_items.id` (CASCADE); `created_by → users.id` (SET NULL)
- **Unique:** `(menu_item_id, alias)`
- **Indexes:** `menu_item_id`; trigram GIN on `alias` — **primary index for menu-item natural-language search**

---

## Section 4 — Semantic Search Embeddings (dedicated tables)

Vector data is never mixed into content/catalog tables anywhere in
this schema. Each embeddable entity gets its own 1:1 embeddings table.

### `menu_item_embeddings`
**Purpose:** Vector representation of a menu item for Semantic Menu Search / Food Recommendation.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| menu_item_id | UUID | No | — | FK → menu_items.id |
| embedding | VECTOR(384) | No | — | dimension TODO, see schema.sql |
| model_version | VARCHAR(100) | No | — | |
| generated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `menu_item_id → menu_items.id` (CASCADE) · **Unique:** `menu_item_id` (1:1)
- **Indexes:** `ivfflat` cosine-similarity index on `embedding` — **semantic search index**

*(`faq_document_embeddings` — same shape, documented in Section 9.)*

---

## Section 5 — Inventory

### `inventory`
**Purpose:** Current stock state for a menu item. `status` is a vendor-dashboard-facing derived summary.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| menu_item_id | UUID | No | — | FK → menu_items.id |
| status | inventory_status_enum | No | `'in_stock'` | in_stock / low_stock / out_of_stock / discontinued |
| quantity_available | INTEGER | No | `0` | |
| quantity_reserved | INTEGER | No | `0` | |
| low_stock_threshold | INTEGER | No | `5` | |
| last_restocked_at | TIMESTAMPTZ | Yes | — | |
| updated_by | UUID | Yes | — | FK → users.id |
| updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `menu_item_id → menu_items.id` (CASCADE); `updated_by → users.id` (SET NULL)
- **Unique:** `menu_item_id` (1:1)
- **Check:** `quantity_available >= 0`; `quantity_reserved >= 0`; `quantity_reserved <= quantity_available`
- **Indexes:** `menu_item_id`; `status` (vendor dashboard low-stock alerts)
- **Relationships:** 1:N → `inventory_logs`

### `inventory_logs`
**Purpose:** Immutable, append-only audit trail of every stock change.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| inventory_id | UUID | No | — | FK → inventory.id |
| change_type | inventory_change_type_enum | No | — | restock / sale / cancellation / adjustment / wastage |
| quantity_delta | INTEGER | No | — | signed |
| reason | TEXT | Yes | — | |
| created_by | UUID | Yes | — | FK → users.id |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `inventory_id → inventory.id` (CASCADE); `created_by → users.id` (SET NULL)
- **Check:** `quantity_delta <> 0` · **Indexes:** `inventory_id`; `created_at`
- **Soft delete:** not applicable — append-only.

---

## Section 6 — Pickup Slots

### `pickup_slots`
**Purpose:** A bookable pickup time window for a stall on a given date.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| slot_date | DATE | No | — | |
| start_time / end_time | TIME | No | — | |
| capacity | INTEGER | No | — | |
| booked_count | INTEGER | No | `0` | |
| status | pickup_slot_status_enum | No | `'open'` | |
| created_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE); `created_by → users.id` (SET NULL)
- **Unique:** `(stall_id, slot_date, start_time, end_time)`
- **Check:** `capacity > 0`; `0 <= booked_count <= capacity`; `start_time < end_time`
- **Indexes:** `(stall_id, slot_date)`; `status`
- **Relationships:** 1:N → `orders`
- **Soft delete:** not applied — time-bound; cancellation via `status`.

---

## Section 7 — Orders & Payments

### `orders`
**Purpose:** A student's food pre-booking against a single stall.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_number | VARCHAR(30) | No | — | human-readable |
| student_id | UUID | No | — | FK → students.user_id |
| stall_id | UUID | No | — | FK → stalls.id |
| pickup_slot_id | UUID | Yes | — | FK → pickup_slots.id |
| status | order_status_enum | No | `'pending_payment'` | |
| placed_via | order_source_enum | No | `'whatsapp'` | |
| subtotal_amount / total_amount | NUMERIC(10,2) | No | — | |
| currency | CHAR(3) | No | `'INR'` | |
| special_instructions | TEXT | Yes | — | |
| cancelled_at / cancelled_reason | — | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `student_id → students.user_id` (RESTRICT); `stall_id → stalls.id` (RESTRICT); `pickup_slot_id → pickup_slots.id` (SET NULL)
- **Unique:** `order_number`
- **Check:** amounts `>= 0`; `status = 'cancelled' ⇒ cancelled_at IS NOT NULL`
- **Indexes:** `(student_id, created_at)` — **order history**; `(stall_id, status)` — **vendor dashboard**; `status`; `created_at`; `pickup_slot_id`
- **Relationships:** 1:N → `order_items`, `order_status_history`, `notifications`, `queue_events`; 1:1 → `payments`, `kitchen_tickets`, `eta_predictions`
- **Soft delete:** not applied — lifecycle via `status` + `order_status_history`.

### `order_items`
**Purpose:** Line items of an order, with a price snapshot at order time.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_id | UUID | No | — | FK → orders.id |
| menu_item_id | UUID | No | — | FK → menu_items.id |
| item_name_snapshot | VARCHAR(150) | No | — | |
| quantity | INTEGER | No | — | |
| unit_price | NUMERIC(10,2) | No | — | snapshot, not live price |
| subtotal | NUMERIC(10,2) | No | — | |
| special_instructions | TEXT | Yes | — | |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `order_id → orders.id` (CASCADE); `menu_item_id → menu_items.id` (RESTRICT)
- **Unique:** `(order_id, menu_item_id)`
- **Check:** `quantity > 0`; `unit_price >= 0`; `subtotal >= 0`
- **Indexes:** `order_id`; `menu_item_id`

### `order_status_history`
**Purpose:** Append-only audit trail of order status transitions, backing WhatsApp tracking updates.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_id | UUID | No | — | FK → orders.id |
| status | order_status_enum | No | — | |
| changed_by | UUID | Yes | — | FK → users.id |
| notes | TEXT | Yes | — | |
| changed_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `order_id → orders.id` (CASCADE); `changed_by → users.id` (SET NULL)
- **Indexes:** `order_id`; `changed_at`

### `payments`
**Purpose:** Payment record for an order (1:1). QR-based UPI is the primary method.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_id | UUID | No | — | FK → orders.id |
| payment_method | payment_method_enum | No | — | upi_qr / card / wallet / cash |
| amount | NUMERIC(10,2) | No | — | |
| currency | CHAR(3) | No | `'INR'` | |
| status | payment_status_enum | No | `'initiated'` | |
| provider | VARCHAR(50) | Yes | — | |
| provider_transaction_id | VARCHAR(150) | Yes | — | |
| qr_code_reference | VARCHAR(255) | Yes | — | |
| paid_at | TIMESTAMPTZ | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `order_id → orders.id` (RESTRICT)
- **Unique:** `order_id` (1:1); `provider_transaction_id`
- **Check:** `amount >= 0` · **Indexes:** `status`; `order_id`
- **Relationships:** 1:N → `payment_refunds`
- **TODO(milestone: payments):** confirm 1:1 vs 1:N retry semantics once a provider is chosen (unresolved by design — see decisions doc).

### `payment_refunds`
**Purpose:** Refund record(s) against a payment.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| payment_id | UUID | No | — | FK → payments.id |
| amount | NUMERIC(10,2) | No | — | |
| reason | TEXT | Yes | — | |
| status | refund_status_enum | No | `'initiated'` | |
| processed_at | TIMESTAMPTZ | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `payment_id → payments.id` (RESTRICT)
- **Check:** `amount > 0` · **Indexes:** `payment_id`

---

## Section 8 — Kitchen Workflow & Queue Engine

### `kitchen_tickets`
**Purpose:** Kitchen-side execution state for an order, decoupled from customer-facing `orders.status`.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_id | UUID | No | — | FK → orders.id |
| stall_id | UUID | No | — | FK → stalls.id |
| status | kitchen_status_enum | No | `'queued'` | |
| priority | SMALLINT | No | `0` | |
| assigned_to | UUID | Yes | — | FK → users.id |
| estimated_ready_at / started_at / completed_at | TIMESTAMPTZ | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `order_id → orders.id` (CASCADE); `stall_id → stalls.id` (RESTRICT); `assigned_to → users.id` (SET NULL)
- **Unique:** `order_id` (1:1)
- **Indexes:** `(stall_id, status)` — **kitchen/vendor dashboard**

### `stall_queues`
**Purpose:** Fast-read, current queue-length snapshot per stall (1:1).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| current_queue_length | INTEGER | No | `0` | |
| average_prep_time_seconds | INTEGER | Yes | — | |
| last_updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE) · **Unique:** `stall_id` (1:1)
- **Check:** `current_queue_length >= 0` · **Indexes:** `stall_id`

### `queue_events`
**Purpose:** Append-only event log feeding queue-length history and ETA model training.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| order_id | UUID | Yes | — | FK → orders.id |
| event_type | queue_event_type_enum | No | — | |
| queue_length_at_event | INTEGER | No | — | |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE); `order_id → orders.id` (SET NULL)
- **Check:** `queue_length_at_event >= 0` · **Indexes:** `(stall_id, created_at)` — **queue analytics**

### `eta_predictions`
**Purpose:** Stores each ETA prediction plus the eventual actual ready time.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| order_id | UUID | No | — | FK → orders.id |
| predicted_ready_at | TIMESTAMPTZ | No | — | |
| predicted_at | TIMESTAMPTZ | No | `now()` | |
| model_version | VARCHAR(100) | No | — | |
| actual_ready_at | TIMESTAMPTZ | Yes | — | |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `order_id → orders.id` (CASCADE) · **Unique:** `order_id` (1:1)

---

## Section 9 — Conversation Sessions

### `conversation_sessions`
**Purpose:** Durable WhatsApp conversation state per user, powering the Intent Engine and LLM tool-calling.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| user_id | UUID | No | — | FK → users.id |
| campus_id | UUID | Yes | — | FK → campuses.id |
| state | conversation_state_enum | No | `'idle'` | |
| current_intent | VARCHAR(100) | Yes | — | |
| selected_stall_id | UUID | Yes | — | FK → stalls.id |
| selected_pickup_slot_id | UUID | Yes | — | FK → pickup_slots.id |
| cart_items | JSONB | No | `'[]'` | temporary pre-order line items |
| draft_order_id | UUID | Yes | — | FK → orders.id, set once checkout starts |
| context | JSONB | No | `'{}'` | free-form Intent Engine slot data |
| is_active | BOOLEAN | No | `TRUE` | |
| last_interaction_at | TIMESTAMPTZ | No | `now()` | |
| expires_at | TIMESTAMPTZ | No | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `user_id → users.id` (CASCADE); `campus_id → campuses.id` (SET NULL); `selected_stall_id → stalls.id` (SET NULL); `selected_pickup_slot_id → pickup_slots.id` (SET NULL); `draft_order_id → orders.id` (SET NULL)
- **Check:** `cart_items` must be a JSON array; `context` must be a JSON object
- **Unique (partial):** `user_id WHERE is_active = TRUE` — enforces exactly one active session per user
- **Indexes:** `user_id`; `expires_at` partial (active only, for expiry sweeps); `state`
- **Soft delete:** not applied — sessions expire via `expires_at`/`is_active`, not deletion, preserving conversation history for AI evaluation.
- **TODO(milestone: AI/conversation layer):** revisit whether `context`'s free-form JSONB needs a stricter, typed companion structure once the Intent Engine's slot-filling schema is finalized.

---

## Section 10 — Notifications

### `notification_templates`
**Purpose:** Reusable message templates per channel/event.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| code | VARCHAR(100) | No | — | |
| channel | notification_channel_enum | No | — | |
| title | VARCHAR(150) | Yes | — | |
| body_template | TEXT | No | — | |
| is_active | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **Unique:** `code` · **Relationships:** 1:N → `notifications`

### `notifications`
**Purpose:** Every outbound message sent to a user, with delivery status tracking.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| user_id | UUID | No | — | FK → users.id |
| order_id | UUID | Yes | — | FK → orders.id |
| template_id | UUID | Yes | — | FK → notification_templates.id |
| channel | notification_channel_enum | No | — | |
| recipient | VARCHAR(255) | No | — | |
| subject | VARCHAR(150) | Yes | — | |
| body | TEXT | No | — | |
| status | notification_status_enum | No | `'pending'` | |
| provider_message_id | VARCHAR(150) | Yes | — | |
| error_message | TEXT | Yes | — | |
| sent_at / delivered_at / read_at | TIMESTAMPTZ | Yes | — | |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `user_id → users.id` (CASCADE); `order_id → orders.id` (SET NULL); `template_id → notification_templates.id` (SET NULL)
- **Indexes:** `(user_id, created_at)`; `order_id`; `status`

---

## Section 11 — Recommendations & Search Analytics

### `recommendation_events`
**Purpose:** Logs every recommendation impression shown to a student and whether it converted.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| student_id | UUID | No | — | FK → students.user_id |
| menu_item_id | UUID | Yes | — | FK → menu_items.id |
| stall_id | UUID | Yes | — | FK → stalls.id |
| recommendation_type | recommendation_type_enum | No | — | |
| score | NUMERIC(5,4) | Yes | — | 0–1 |
| context | JSONB | Yes | — | |
| shown_at | TIMESTAMPTZ | No | `now()` | |
| clicked | BOOLEAN | No | `FALSE` | |
| clicked_at | TIMESTAMPTZ | Yes | — | |
| converted_order_id | UUID | Yes | — | FK → orders.id |

- **PK:** `id` · **FK:** `student_id → students.user_id` (CASCADE); `menu_item_id → menu_items.id` (SET NULL); `stall_id → stalls.id` (SET NULL); `converted_order_id → orders.id` (SET NULL)
- **Check:** `score BETWEEN 0 AND 1` if set; at least one of `menu_item_id`/`stall_id` set
- **Indexes:** `(student_id, shown_at)`

### `search_queries`
**Purpose:** Logs every search issued for Campus-aware Search analytics.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| user_id | UUID | Yes | — | FK → users.id |
| campus_id | UUID | Yes | — | FK → campuses.id |
| query_text | TEXT | No | — | |
| query_type | search_query_type_enum | No | — | |
| results_count | INTEGER | No | `0` | |
| created_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `user_id → users.id` (SET NULL); `campus_id → campuses.id` (SET NULL)
- **Check:** `results_count >= 0` · **Indexes:** `(campus_id, created_at)` — **analytics**; `created_at`

### `faq_documents`
**Purpose:** Knowledge-base source documents for the RAG-based FAQ. Vector data lives separately (see `faq_document_embeddings`).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| campus_id | UUID | Yes | — | FK → campuses.id; NULL = platform-wide |
| title | VARCHAR(255) | No | — | |
| content | TEXT | No | — | |
| source_url | VARCHAR(500) | Yes | — | |
| is_active | BOOLEAN | No | `TRUE` | |
| created_by / updated_by | UUID | Yes | — | FK → users.id |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |
| deleted_at | TIMESTAMPTZ | Yes | — | soft delete |

- **PK:** `id` · **FK:** `campus_id → campuses.id` (CASCADE) · **Indexes:** `campus_id`
- **Relationships:** 1:1 → `faq_document_embeddings`

### `faq_document_embeddings`
**Purpose:** Vector representation of a FAQ document for RAG retrieval.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| faq_document_id | UUID | No | — | FK → faq_documents.id |
| embedding | VECTOR(384) | No | — | dimension TODO |
| model_version | VARCHAR(100) | No | — | |
| generated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `faq_document_id → faq_documents.id` (CASCADE) · **Unique:** `faq_document_id` (1:1)
- **Indexes:** `ivfflat` cosine-similarity index on `embedding` — **RAG semantic search**

---

## Section 12 — Analytics

### `daily_stall_analytics`
**Purpose:** Pre-aggregated per-stall, per-day rollup for vendor/admin dashboards.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | UUID | No | `gen_random_uuid()` | PK |
| stall_id | UUID | No | — | FK → stalls.id |
| analytics_date | DATE | No | — | |
| total_orders | INTEGER | No | `0` | |
| total_revenue | NUMERIC(12,2) | No | `0` | |
| cancelled_orders | INTEGER | No | `0` | |
| average_prep_time_seconds | INTEGER | Yes | — | |
| created_at / updated_at | TIMESTAMPTZ | No | `now()` | |

- **PK:** `id` · **FK:** `stall_id → stalls.id` (CASCADE)
- **Unique:** `(stall_id, analytics_date)`
- **Check:** all totals `>= 0`
- **Indexes:** `(stall_id, analytics_date)`; `analytics_date`
- **Note:** populated by a scheduled aggregation job; implementation deferred (TODO, future milestone).

---

## Indexing Strategy — Requirement-to-Index Map

| Requirement | Index(es) |
|---|---|
| Campus search | `ix_campuses_name_trgm` |
| Location lookup | `ix_locations_campus_id`, `ix_locations_campus_type` |
| Nearby stall lookup | `ix_locations_coordinates`, `ix_stalls_location_id` (see decisions doc re: deferred true radius search) |
| Natural language search | `ix_stall_search_aliases_alias_trgm`, `ix_menu_item_search_aliases_alias_trgm`, `ix_location_aliases_alias_trgm`, `ix_stalls_name_trgm`, `ix_menu_items_name_trgm` |
| Semantic search | `ix_menu_item_embeddings_vector`, `ix_faq_document_embeddings_vector` |
| Vendor dashboard | `ix_stalls_vendor_id`, `ix_orders_stall_status`, `ix_kitchen_tickets_stall_status`, `ix_inventory_status` |
| Order history | `ix_orders_student_id` (composite with `created_at`) |
| Analytics | `ix_daily_stall_analytics_stall_date`, `ix_daily_stall_analytics_date`, `ix_search_queries_campus_created` |
| Queue | `ix_stall_queues_stall_id`, `ix_queue_events_stall_id` (composite with `created_at`) |

---

## Table Inventory Summary (34 tables)

| # | Table | Section | # | Table | Section |
|---|---|---|---|---|---|
| 1 | users | Identity | 18 | order_items | Orders & Payments |
| 2 | campuses | Identity | 19 | order_status_history | Orders & Payments |
| 3 | students | Identity | 20 | payments | Orders & Payments |
| 4 | vendors | Identity | 21 | payment_refunds | Orders & Payments |
| 5 | admins | Identity | 22 | kitchen_tickets | Kitchen & Queue |
| 6 | locations | Campus Locations | 23 | stall_queues | Kitchen & Queue |
| 7 | location_aliases | Campus Locations | 24 | queue_events | Kitchen & Queue |
| 8 | stalls | Stalls & Catalog | 25 | eta_predictions | Kitchen & Queue |
| 9 | stall_search_aliases | Stalls & Catalog | 26 | conversation_sessions | Conversation Sessions |
| 10 | stall_operating_hours | Stalls & Catalog | 27 | notification_templates | Notifications |
| 11 | menu_categories | Stalls & Catalog | 28 | notifications | Notifications |
| 12 | menu_items | Stalls & Catalog | 29 | recommendation_events | Recommendations & Search |
| 13 | menu_item_search_aliases | Stalls & Catalog | 30 | search_queries | Recommendations & Search |
| 14 | menu_item_embeddings | Embeddings | 31 | faq_documents | Recommendations & Search |
| 15 | inventory | Inventory | 32 | faq_document_embeddings | Recommendations & Search |
| 16 | inventory_logs | Inventory | 33 | daily_stall_analytics | Analytics |
| 17 | pickup_slots | Pickup Slots | 34 | orders | Orders & Payments |
