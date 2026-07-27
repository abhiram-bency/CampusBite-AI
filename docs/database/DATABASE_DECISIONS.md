# DATABASE_DECISIONS.md — CampusBite AI

**Milestone 2 (Revised / FINAL): Database Architecture**
This document records the reasoning behind non-obvious schema
decisions. Per Project Rule #6, this design is **frozen** once
accepted — treat every decision below as binding for all future
implementation milestones unless a `TODO` explicitly says otherwise.

---

## Revision notes (diff against the prior schema.sql/enums.sql)

This milestone's requirements added detail the earlier pass didn't
have. Changes made:

**New tables:** `location_aliases`, `stall_search_aliases`,
`menu_item_search_aliases`, `conversation_sessions`,
`faq_document_embeddings`.

**Split out:** `faq_documents.embedding` moved into its own
`faq_document_embeddings` table, for the same reason
`menu_item_embeddings` was already separate — "never mix vector data
into content tables" now applies uniformly.

**Renamed (naming-convention alignment with this milestone's explicit
enum list):**
- `slot_status_enum` → `pickup_slot_status_enum`
- `kitchen_ticket_status_enum` → `kitchen_status_enum`

**New enums:** `inventory_status_enum`, `conversation_state_enum`,
`food_type_enum`.

**Column changes:** `menu_items.is_vegetarian` + `menu_items.is_vegan`
(two booleans) replaced by `menu_items.food_type` (one enum) — see §16.
`inventory.status` added (derived, dashboard-facing). `created_by`/
`updated_by` audit columns added to every table a vendor/admin
directly edits (`campuses`, `locations`, `stalls`, `menu_categories`,
`menu_items`, `pickup_slots`, `notification_templates`,
`faq_documents`, plus `created_by` on the three alias tables).

**Not changed:** the core identity model (§2), the flexible
`locations` model (§4), the price-snapshot decision (§6), the
kitchen/order status split (§7), the queue snapshot/log split (§8),
and the soft-delete policy (§10) all carry over unchanged from the
prior revision — they were already correct for these requirements.

**Table count:** 29 → 34.

---

## 1. Primary key strategy: UUID everywhere

**Decision:** every table uses `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` (subtype tables like `students`/`vendors`/`admins` reuse `users.id` as their PK).

**Why:** matches the already-completed infrastructure milestone (`app/database/base.py`, `mixins.py`) — a backward-compatibility requirement, not a fresh choice. UUIDs are also safe to generate client-side (useful for the WhatsApp conversation layer referencing an order before a DB round-trip completes) and don't leak row-count information via sequential IDs.

---

## 2. Supertype/subtype identity model (`users` + `students`/`vendors`/`admins`)

**Decision:** one root `users` table with fields common to every actor, plus three 1:1 subtype tables for role-specific fields.

**Why:** a flat `users` table with nullable vendor/admin/student columns would violate 3NF (columns relevant only depending on `role`) and accumulate NULLs as roles grow. Role-specific rules (e.g. `registration_number` uniqueness, `admin_level`) stay scoped to their own table.

**Known gap:** Postgres cannot cheaply enforce "exactly one subtype row exists, matching `users.role`" declaratively. Left as a service-layer invariant for a future milestone, not solved with an over-engineered trigger here.

---

## 3. Multi-campus support (`campuses` table)

**Decision:** `campuses` is the tenant root, scoping `locations`, `students`, and (optionally) `admins`.

**Why:** the project overview refers to "university campuses" (plural), and Campus-aware Search / Navigator are named AI features. This is a data-modeling necessity, not an architecture change — the frozen Conversation → Intent Engine → Domain Services → Repositories → PostgreSQL layering is untouched, and no folders/modules were renamed or moved.

---

## 4. Flexible `locations` model instead of `blocks`

**Decision:** `locations` uses `location_type_enum` (`block`, `nearby_block`, `building`, `landmark`, `outdoor_area`, `open_space`) plus a free-text `reference_label`, rather than a `blocks` table stalls reference by `block_id`.

**Why:** explicitly required — stalls are frequently positioned relative to a block ("Near Block 34") or an unnamed area ("open space near the ground") rather than inside a formal structure. `latitude`/`longitude` are included now (nullable) so precise geolocation can be added later without a migration touching every stall — only `locations` needs backfilling.

---

## 5. `stalls` does not duplicate `campus_id`

**Decision:** a stall's campus is derived via `stalls.location_id → locations.id → locations.campus_id`. No direct `campus_id` on `stalls`.

**Why (3NF):** `campus_id` is functionally dependent on `location_id`, not on `stalls.id` — storing it on both would be a transitive dependency and an update anomaly (a relocated stall could retain a stale campus).

**Tradeoff acknowledged:** campus-scoped stall queries need a join through `locations`. Given `locations` is small and low-churn, and is indexed (`ix_locations_campus_id`, `ix_locations_campus_type`), this join is cheap. If it ever isn't, the fix is a **materialized view**, not denormalizing the base table — deferred as a future optimization.

---

## 6. Price snapshot on `order_items` (the one necessary denormalization)

**Decision:** `order_items.unit_price` and `item_name_snapshot` duplicate `menu_items.price` / `menu_items.name` at order time.

**Why:** order history must be immutable — a vendor's price change next week must not silently rewrite last week's receipts. This is the schema's single deliberate exception to strict normalization, and it exists because there is no other way to keep historical records accurate without a temporal `menu_items` history table, which nothing else in the schema needs.

---

## 7. Kitchen ticket status is separate from order status

**Decision:** `orders.status` (customer-facing) and `kitchen_tickets.status` (kitchen-facing, `kitchen_status_enum`) are distinct state machines.

**Why:** different audiences, different rates of change. Kitchen operations can evolve (e.g. adding a "plating" stage) without changing the WhatsApp-facing contract students see.

---

## 8. Queue engine: snapshot table + event log, not one table

**Decision:** `stall_queues` (1 row per stall, overwritten in place) is separate from `queue_events` (append-only log).

**Why:** different access patterns — `stall_queues` answers "what's the queue right now?" in O(1) for every WhatsApp status check; `queue_events` exists for ETA-model training/evaluation, a batch workload. Merging them would compromise both.

---

## 9. `eta_predictions` stores both predicted and actual outcomes

**Decision:** one row per order holding `predicted_ready_at` and (once known) `actual_ready_at`.

**Why:** an ETA model is worthless without a ground-truth feedback loop; keeping both in one row makes "was this prediction accurate?" and the eventual training dataset a single table scan.

---

## 10. Soft-delete policy

**Decision:** `deleted_at` applied only to master/reference tables: `users`, `campuses`, `students`, `vendors`, `admins`, `locations`, `stalls`, `menu_categories`, `menu_items`, `faq_documents`.

**Not applied to:** `orders`, `order_items`, `order_status_history`, `payments`, `payment_refunds`, `inventory_logs`, `queue_events`, `notifications`, `recommendation_events`, `search_queries`, `pickup_slots`, `kitchen_tickets`, `stall_operating_hours`, `stall_queues`, `eta_predictions`, `daily_stall_analytics`, `location_aliases`, `stall_search_aliases`, `menu_item_search_aliases`, `conversation_sessions`, `faq_document_embeddings`, `menu_item_embeddings`.

**Why:** the second group are transactional records, append-only logs, or ephemeral/derived state — they represent *what happened* (must stay permanent for audit/financial integrity) or are cheap to simply add/remove outright (aliases, sessions). Applying soft-delete uniformly "for consistency" would blur that distinction and force every analytics query to remember a `deleted_at IS NULL` filter that can never actually be false.

---

## 11. ENUM types vs. lookup tables vs. free text

**Decision:** fixed, small, slow-changing vocabularies (`order_status`, `kitchen_status`, `location_type`, `food_type`, etc.) are native PostgreSQL `ENUM` types. Higher-cardinality or user-editable vocabularies (`cuisine_type`, `department`) remain plain `VARCHAR`.

**Why:** enums give compile-time-like safety and cheaper comparisons than a joined lookup table, appropriate for values that only change via a schema migration (a new order status is a product decision). Free-text fields are for genuinely open-ended, frequently-added values where a migration per new value would be friction for no safety benefit.

**Known limitation:** adding an enum value later requires `ALTER TYPE ... ADD VALUE`, which has transactional restrictions in some Postgres versions. Acceptable given how rarely these vocabularies change.

---

## 12. pgvector for embeddings, in dedicated tables, inside PostgreSQL

**Decision:** `menu_item_embeddings` and `faq_document_embeddings` use the `vector` type (pgvector) with `ivfflat` cosine-similarity indexes. Both are separate 1:1 tables — **never a column on the content table itself.**

**Why "dedicated tables":** explicitly required this milestone ("do not mix vector data into menu tables") and generalized to FAQ documents for the same underlying reason: embeddings have a different write pattern (offline batch regeneration when a model changes) than the content rows they describe (edited interactively by vendors/admins), and mixing them forces every `SELECT *` on the content table to pull a 384-dimension vector it usually doesn't need.

**Why "inside PostgreSQL":** the project's AI rule is "the AI never directly queries PostgreSQL — it only calls backend tools." Storing embeddings in Postgres doesn't violate that: the **Repository layer** queries them on the AI layer's behalf via a Domain Service tool call — identical access pattern to every other table. This avoids running a second specialized vector database for this milestone's needs, while remaining compatible with FAISS being used as an in-memory serving-time index built *from* this data later.

**TODO(milestone: AI/search):** confirm final embedding dimension (384 assumed, `all-MiniLM-L6-v2`-class) once the model is chosen.

---

## 13. `payments` is 1:1 with `orders` (for now)

**Decision:** `payments.order_id` is unique; a payment transitions through statuses rather than getting a new row per attempt.

**TODO(milestone: payments):** relax to 1:N if the eventual provider's retry/webhook model makes separate rows more natural. Deliberately left open rather than guessed at.

---

## 14. Normalized alias tables, not JSON/array columns

**Decision:** `location_aliases`, `stall_search_aliases`, and `menu_item_search_aliases` are each a separate table with one row per alias, FK'd back to the entity they describe.

**Why:** explicitly required this milestone ("Do NOT store aliases inside a JSON field or array. Normalize them into a separate table."). Beyond compliance, it's the objectively better design for the stated purpose: each alias needs to be independently indexed (`gin_trgm_ops`) for fast natural-language matching — a JSONB array would force a full scan or a functional index over `jsonb_array_elements`, which is slower and harder to reason about than a plain indexed column. It also lets a future auth/audit milestone track *who added which alias and when* (`created_by`, `created_at`) at alias granularity, which a shared array column can't do.

**Consistency:** all three alias tables follow the identical shape (`id`, `<parent>_id`, `alias`, `created_by`, `created_at`, `updated_at`, unique `(<parent>_id, alias)`, trigram GIN index on `alias`) so a future Repository layer can implement one generic alias-lookup pattern reused across all three, rather than three bespoke ones.

---

## 15. `conversation_sessions`: state machine + JSONB context, not a table per intent

**Decision:** one table holds a small, stable `state` enum (`conversation_state_enum`) plus two JSONB columns: `cart_items` (array) for the in-progress order being built, and `context` (object) for free-form Intent Engine slot data. Exactly one active session per user is enforced by a **partial unique index on `is_active`**, not a check against `now()`.

**Why one table, not one-table-per-intent:** the set of possible conversational intents (browse, search, order, cancel, FAQ, escalate) will keep growing as the AI layer matures. Modeling each as its own table would mean a schema migration every time the Intent Engine learns a new capability. A stable coarse `state` plus flexible `context` lets the AI/conversation-layer milestone iterate on slot-filling structure without touching the database schema — appropriate because, per the frozen architecture, **the AI never queries PostgreSQL directly**; it only ever sees `context` through whatever shape a Domain Service tool chooses to expose, so the raw JSONB flexibility here has no leakage risk to the AI layer's contract.

**Why `cart_items` is JSONB and not rows in a table:** before checkout, the "order" isn't a real business entity yet — it's a conversational draft that can be abandoned, edited, or restarted mid-conversation. Modeling it with a formal `draft_order_items` table would mean every WhatsApp message that adds/removes an item is a full transactional insert/delete against a durable table, for state that's discarded the moment the student changes their mind. JSONB inside the session row is the right weight for genuinely transient state; the durable, permanent version of the same information (`order_items`) is a real normalized table, because *that* data must never be lost or silently rewritten.

**Why a partial unique index instead of a `CHECK`:** Postgres `CHECK` constraints must be immutable and cannot reference other rows or call `now()`; "only one active session per user" is an aggregate constraint across rows, which only a unique index (partial, on `is_active = TRUE`) can express declaratively.

**TODO(milestone: AI/conversation layer):** if `context`'s free-form shape proves too loose once the Intent Engine's actual slot-filling schema is finalized, consider a stricter typed structure then — not guessed at now.

---

## 16. `food_type` enum replaces `is_vegetarian`/`is_vegan` booleans

**Decision:** `menu_items.food_type` (`veg` / `non_veg` / `egg` / `vegan`) is a single enum, replacing the two-boolean pair from the prior schema revision.

**Why:** this milestone explicitly asks for a `Food Type` ENUM. Beyond compliance, the boolean pair had a latent data-integrity gap the earlier revision patched with a `CHECK` (`is_vegan ⇒ is_vegetarian`) rather than actually preventing — two independent booleans can still represent a nonsensical combination unless every reader remembers the implication. A single exhaustive, mutually-exclusive enum makes invalid combinations structurally unrepresentable instead of merely checked.

**Reused, not duplicated:** `students.dietary_preference` reuses the same `food_type_enum` rather than introducing a near-identical second enum, since a student's stated preference and a dish's classification are the same underlying vocabulary.

---

## 17. Normalization summary (1NF / 2NF / 3NF)

**1NF — atomic values, no repeating groups:**
Every column holds a single scalar value (or a `JSONB` value explicitly chosen for genuinely semi-structured, non-relational data — `conversation_sessions.context`/`cart_items`, `recommendation_events.context` — never as a substitute for a proper relation; see §14 for why aliases are *not* JSON). No table has repeating "item 1 / item 2 / item 3" columns: weekly hours are rows in `stall_operating_hours`, order lines are rows in `order_items`, aliases are rows in the three alias tables.

**2NF — no partial dependency on a composite key:**
Every table uses a single-column primary key (`id`, or the FK'd `user_id` for subtype tables), so partial-key dependency cannot occur by construction. Composite *unique constraints* exist (e.g. `(stall_id, day_of_week)`, `(order_id, menu_item_id)`) but are not primary keys, so 2NF is satisfied trivially and by design.

**3NF — no transitive dependency on a non-key attribute:**
Checked table-by-table; the two intentional, documented exceptions are:
1. `order_items.unit_price` / `item_name_snapshot` — historical snapshot, not a live functional dependency (§6).
2. None else. `stalls` was specifically kept **without** a duplicated `campus_id` to avoid a second exception (§5). `inventory.status` is a derived/cached summary of `quantity_available`/`quantity_reserved`, kept in sync by the service layer rather than stored redundantly by a trigger at this stage — flagged here as a soft, acknowledged 3NF tension (the *value* of `status` is technically determinable from the quantity columns) accepted because it's the standard, intentional "materialized derived status" pattern used for dashboard-facing fields, not an accidental duplication of independently-editable facts.

---

## 18. What was deliberately left out (and why)

Per the standing instruction ("if something appears missing, leave a
TODO instead of inventing a new architecture"):

- **Authentication/session tables** (OTP codes, JWT refresh tokens) — a future authentication milestone. `conversation_sessions` is *not* an auth session table — it models WhatsApp conversational state, not login credentials; the two are unrelated concerns that happen to share the word "session."
- **Menu item modifiers/add-ons** (e.g. "extra cheese") — not named in this milestone's table list; would be scope creep.
- **True geospatial radius search** (PostGIS / earthdistance) — `latitude`/`longitude` columns and a supporting index exist, but proximity ranking itself is left to the application layer for now; a dedicated extension is a future optimization once real coordinates exist.
- **Multi-language content** — no i18n columns/tables; out of scope.
- **Materialized search/analytics views** — referenced in §5 as a future optimization if the `locations` join ever becomes a bottleneck; not built now, since this milestone is schema design, not performance tuning.
