# CampusBite AI Backend
## 06_SQLALCHEMY_GUIDE.md

Version: 1.0

Status: Database ORM Development Guide

---

# Purpose

This document defines how SQLAlchemy must be used throughout the CampusBite AI Backend.

Every repository, model, relationship, query, transaction, and migration must follow these conventions.

The objective is to maintain a clean, scalable, and predictable ORM layer while preserving strict separation between business logic and persistence.

---

# SQLAlchemy Version

The project uses

```
SQLAlchemy 2.x
```

with

```
Async ORM
```

Never use legacy SQLAlchemy APIs.

---

# Database Architecture

The database layer follows

```
Router
    │
    ▼
Service
    │
    ▼
Repository
    │
    ▼
SQLAlchemy ORM
    │
    ▼
PostgreSQL
```

Business logic must never reach the ORM directly.

---

# Async First

Every database interaction must be asynchronous.

Always use

```python
AsyncSession
```

Never use

```python
Session
```

---

# Session Ownership

Sessions are request-scoped.

Created once.

Shared through dependency injection.

Disposed automatically.

Repositories receive sessions.

Repositories never create sessions.

---

# Transaction Lifecycle

One request

↓

One transaction

↓

Automatic commit

↓

Automatic rollback on failure

Repositories must never call

```python
commit()
```

or

```python
rollback()
```

---

# Repository Responsibility

Repositories own

- SELECT
- INSERT
- UPDATE
- DELETE
- flush()
- refresh()

Repositories do not own

- business rules
- JWT
- authentication
- validation
- authorization
- HTTP

---

# Query Style

Always use SQLAlchemy 2.x syntax.

Correct

```python
stmt = select(User).where(
    User.id == user_id
)

result = await session.execute(stmt)

user = result.scalar_one_or_none()
```

Never use

```python
session.query(...)
```

---

# Filtering

Use

```python
.where()
```

Example

```python
stmt = select(User).where(
    User.email == email
)
```

Multiple filters

```python
stmt = select(User).where(
    User.email == email,
    User.deleted_at.is_(None),
)
```

---

# Ordering

Use

```python
.order_by()
```

Example

```python
stmt = (
    select(Stall)
    .order_by(Stall.created_at.desc())
)
```

---

# Pagination

Use

```python
.limit()

.offset()
```

Example

```python
stmt = (
    select(Stall)
    .limit(limit)
    .offset(offset)
)
```

---

# Selecting Columns

When only one column is needed

Prefer

```python
select(User.id)
```

instead of

```python
select(User)
```

This reduces memory usage.

---

# Existence Checks

Correct

```python
stmt = select(User.id).where(
    User.email == email
)

exists = (
    await session.execute(stmt)
).scalar_one_or_none() is not None
```

Avoid loading entire ORM objects unnecessarily.

---

# Inserts

Repositories create ORM objects.

Example

```python
user = User(
    email=email,
    full_name=full_name,
)

session.add(user)
```

Do not commit.

---

# Updates

Update ORM attributes directly.

Example

```python
user.full_name = payload.full_name
```

Then

```python
await session.flush()

await session.refresh(user)
```

---

# Deletes

Prefer soft delete whenever supported.

Example

```python
user.deleted_at = utcnow()
```

Only use physical delete when explicitly required.

---

# Soft Delete Policy

Models inheriting

```
SoftDeleteMixin
```

must exclude deleted rows by default.

Example

```python
.where(
    User.deleted_at.is_(None)
)
```

Repositories should consistently enforce this.

---

# Flush vs Commit

Repositories may call

```python
flush()
```

Repositories may call

```python
refresh()
```

Repositories must never call

```python
commit()
```

---

# Refresh

Refresh after flush if database-generated values are required.

Example

```python
await session.flush()

await session.refresh(user)
```

---

# UUID Usage

All primary keys use

```
UUID
```

Type

```python
UUID(as_uuid=True)
```

Never use integer IDs.

---

# Relationships

Relationships belong in models.

Example

```python
user = relationship(
    "User",
    back_populates="vendor",
)
```

Repositories should not manually reconstruct relationships.

---

# Lazy Loading

Prefer explicit loading.

Avoid accidental lazy loading in async code.

Use

```python
selectinload()

joinedload()
```

when necessary.

---

# Joined Loading

Example

```python
stmt = (
    select(Stall)
    .options(
        selectinload(Stall.vendor)
    )
)
```

Use only when related objects are required.

---

# N+1 Queries

Avoid patterns like

```
Load list

↓

Loop

↓

One query each iteration
```

Instead

Use eager loading.

---

# Model Design

Models contain

- columns
- relationships
- __repr__

Models do not contain

- HTTP logic
- business logic
- SQL queries
- JWT logic

---

# Naming

Tables

Plural

Example

```
users

vendors

stalls

bookings
```

Classes

Singular

```
User

Vendor

Booking
```

---

# Column Naming

Use descriptive names.

Good

```
business_registration_no

registration_number

phone_number
```

Avoid abbreviations.

---

# Foreign Keys

Always declare explicitly.

Example

```python
ForeignKey(
    "users.id",
    ondelete="CASCADE",
)
```

---

# Cascade Rules

Specify intentionally.

Examples

```
CASCADE

SET NULL

RESTRICT
```

Never rely on defaults.

---

# Constraints

Prefer database constraints.

Examples

Unique

```python
unique=True
```

Check

```python
CheckConstraint(...)
```

Foreign keys

```
ForeignKey(...)
```

Business rules still belong in services.

---

# Enums

Use PostgreSQL enums.

Python

```python
UserRoleEnum
```

Database

```
user_role_enum
```

Never compare raw strings.

---

# Timestamps

Use

```
TimestampMixin
```

Every mutable table should have

```
created_at

updated_at
```

---

# Audit Fields

Examples

```
verified_by

approved_by

deleted_at
```

Always use UUID foreign keys.

---

# Repository Return Types

Repositories return

ORM models

or

None

Never return dictionaries.

---

# Error Handling

Repositories should not catch business exceptions.

Unexpected database errors propagate upward.

Services translate business failures.

Routers translate HTTP failures.

---

# Raw SQL

Avoid raw SQL.

Only use when

- performance requires it
- SQLAlchemy cannot express the query cleanly

Document why.

---

# Alembic

All schema changes use

```
Alembic
```

Never manually edit production databases.

Migration workflow

```
Modify models

↓

Generate migration

↓

Review migration

↓

Apply migration
```

---

# Model Imports

Avoid circular imports.

Use

```python
from __future__ import annotations
```

Relationship targets may use strings.

Example

```python
relationship(
    "Vendor"
)
```

---

# Performance Guidelines

Prefer

```
SELECT required columns

↓

LIMIT

↓

INDEXED filters

↓

Eager loading only when necessary
```

Avoid

```
SELECT *

Loading entire tables

Repeated queries

Unused relationships
```

---

# Testing

Repository tests should verify

- insert
- lookup
- update
- delete
- soft delete
- relationship loading

Prefer integration tests with PostgreSQL.

---

# AI Development Rules

When generating repository code

Always

- use AsyncSession
- use SQLAlchemy 2.x syntax
- return ORM models
- use flush() instead of commit()
- keep repositories free of business logic

Never

- import FastAPI
- raise HTTPException
- hash passwords
- create JWTs
- perform authorization
- instantiate sessions

---

# Common Repository Pattern

```python
class UserRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )

        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()
```

---

# Golden Rules

1. SQLAlchemy belongs only in repositories.

2. Services never execute SQL.

3. Routers never access the database.

4. Never commit inside repositories.

5. Always use AsyncSession.

6. Use SQLAlchemy 2.x syntax only.

7. Prefer ORM over raw SQL.

8. Soft-delete records should be excluded by default.

9. Keep one request as one transaction.

10. Repository code should be small, predictable, and completely free of business logic.

This document is the canonical SQLAlchemy development guide for the CampusBite AI Backend.