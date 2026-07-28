# CampusBite AI Backend
## 03_DATABASE.md

Version: 1.0

Status: Canonical Database Design Rules

---

# Purpose

This document defines the **database architecture**, ownership rules, naming conventions, transaction boundaries, and SQLAlchemy usage for the CampusBite AI Backend.

Every AI assistant working on this project **must follow this document** before generating models, repositories, migrations, or queries.

The database schema is considered the **single source of truth**.

---

# Database Technology

Database

- PostgreSQL 17+

ORM

- SQLAlchemy 2.x (Async)

Driver

- asyncpg

Migration Tool

- Alembic

---

# Design Philosophy

The database follows a normalized relational design.

Goals

- Strong data integrity
- Minimal duplication
- Predictable relationships
- Clear ownership
- Fast indexed queries
- Transaction safety

---

# Database Layers

```
FastAPI Router

↓

Service Layer

↓

Repository Layer

↓

SQLAlchemy ORM

↓

PostgreSQL
```

Only repositories may execute SQL.

Services never execute SQL.

Routers never execute SQL.

---

# UUID Policy

Every primary key uses UUID.

Example

```python
id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
)
```

Never use

- Integer IDs
- Auto increment IDs

---

# Timestamp Policy

Every persistent table inherits TimestampMixin.

Fields

```
created_at

updated_at
```

These are automatically maintained.

Never manually update timestamps.

---

# Soft Delete Policy

Business entities use SoftDeleteMixin.

Fields

```
deleted_at
```

Records are never physically deleted unless explicitly required.

Repositories should ignore soft-deleted rows unless the feature specifically requires them.

Example

```python
select(User).where(User.deleted_at.is_(None))
```

---

# Audit Fields

Where appropriate, tables should contain audit information.

Examples

```
verified_by

approved_by

created_by

updated_by
```

Audit fields store UUID references.

Avoid unnecessary relationship() definitions for audit-only foreign keys.

---

# Relationship Ownership

Each relationship has exactly one owner.

Example

```
User

↓

Vendor

↓

Stall

↓

Menu Item
```

Ownership should always flow downward.

---

# One-to-One Relationships

Example

```
users

↓

vendors
```

```
users

↓

students
```

Use

```
user_id
```

as both

- Primary Key

and

- Foreign Key

Example

```python
user_id = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id"),
    primary_key=True,
)
```

---

# One-to-Many Relationships

Example

```
Vendor

↓

Stalls
```

One vendor

Many stalls

---

# Many-to-Many Relationships

Never create direct many-to-many relationships.

Always create junction tables.

Example

```
students

↓

favorite_items

↓

menu_items
```

---

# Naming Convention

Tables

Plural

Examples

```
users

vendors

students

stalls

orders

payments
```

Columns

snake_case

Examples

```
business_name

registration_number

phone_number
```

Constraints

```
ck_

fk_

uq_

ix_
```

Examples

```
ck_users_phone_number

uq_users_email

ix_orders_status
```

---

# Foreign Keys

Always specify ON DELETE behavior.

Examples

```python
CASCADE

SET NULL

RESTRICT
```

Never rely on defaults.

---

# Check Constraints

Validation should exist in both

Pydantic

AND

Database.

Example

```
Phone Number

↓

Pydantic regex

↓

Database CHECK constraint
```

Never rely on only one layer.

---

# Unique Constraints

Examples

```
email

registration_number

business_registration_number
```

Uniqueness belongs in the database.

The service layer only converts database/business conditions into domain exceptions.

---

# Index Policy

Index every

Primary key

Foreign key

Frequently searched column

Examples

```
email

status

created_at

vendor_id

campus_id
```

Avoid unnecessary indexes.

Indexes slow writes.

---

# Transactions

Transaction ownership belongs to the request-scoped AsyncSession.

Repositories

Never commit.

Never rollback.

Services

Never commit.

Routers

Never commit.

The request lifecycle performs one commit.

Example

```
Request

↓

Repository

↓

Repository

↓

Repository

↓

Automatic Commit
```

---

# Repository Rules

Repositories may

SELECT

INSERT

UPDATE

DELETE (soft delete)

FLUSH

REFRESH

Repositories may not

commit()

rollback()

contain business logic

issue JWTs

verify passwords

---

# Flush Policy

Repositories may call

```python
await session.flush()
```

only when

- generated values are required

- refreshed objects are needed

Never flush after every INSERT.

---

# Refresh Policy

Use

```python
await session.refresh(model)
```

only when necessary.

Do not refresh everything automatically.

---

# Model Responsibilities

Models represent persistence only.

Models should never contain

Business logic

Authentication

Authorization

Validation

HTTP concepts

Logging

---

# Relationship Loading

Default

```
lazy="select"
```

Use eager loading only when profiling proves necessary.

Avoid premature optimization.

---

# Enum Policy

Database enums mirror Python enums.

Example

```
UserRoleEnum

↓

user_role_enum
```

Never duplicate enum values as strings.

---

# Authentication Data

Users table stores

```
password_hash

email

role

phone_number
```

Never store

JWTs

refresh tokens

OTP codes

plaintext passwords

---

# Vendor Data

Vendor profile stores

```
business_name

business_registration_no

verified_at

verified_by
```

Vendor campus is **not stored**.

Campus is derived from

```
Vendor

↓

Stall

↓

Location

↓

Campus
```

---

# Student Data

Students store

```
registration_number

campus_id
```

Registration number is globally unique.

---

# Order Lifecycle

Orders should support

```
Pending

Accepted

Preparing

Ready

Completed

Cancelled
```

Never delete completed orders.

---

# Payment Records

Payments are immutable.

Never overwrite historical payment records.

Instead

Create new payment events.

---

# Logging

Repositories never log successful SELECT statements.

Repositories may log

Unexpected failures

Constraint violations

Database exceptions

Business logging belongs in services.

---

# Migrations

Every schema change requires

Alembic migration

Migration review

Upgrade

Downgrade

Never manually edit production databases.

---

# Testing

Repository tests

Use isolated test databases.

Service tests

Mock repositories.

Router tests

Override dependencies.

---

# Performance Rules

Avoid

N+1 queries

Repeated SELECTs

Repeated commits

Large eager loads

Measure performance before optimizing.

---

# Database Ownership Summary

| Layer | Responsibility |
|---------|----------------|
| Model | Table definition |
| Repository | Database access |
| Service | Business rules |
| Router | HTTP |
| Migration | Schema evolution |

---

# Future Tables

Expected future schema additions

```
reviews

inventory

inventory_transactions

coupons

coupon_redemptions

notifications

recommendations

embeddings

chat_sessions

chat_messages

analytics_events

audit_logs

kitchen_queue

delivery_assignments
```

Each future table must follow every rule in this document.

---

# Golden Rules

1. PostgreSQL is the source of truth.

2. Every primary key is UUID.

3. Every repository owns SQL.

4. Services never execute SQL.

5. Routers never execute SQL.

6. No repository imports another repository.

7. Never commit inside repositories.

8. Never duplicate validation.

9. Always use Alembic migrations.

10. Optimize only after measuring.

This document is the canonical database specification for the CampusBite AI Backend.