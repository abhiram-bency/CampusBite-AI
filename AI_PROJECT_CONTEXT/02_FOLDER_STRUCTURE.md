# CampusBite AI Backend
## Folder Structure & Module Organization

Version: 1.0
Status: Canonical Project Structure

---

# Philosophy

This project follows **Domain Driven Modular Architecture**.

Every business domain owns:

- its own router
- service
- repository
- schemas
- exceptions
- dependencies
- tests

No module should depend directly on another module's repository.

Communication should happen through:

- services
- models
- dependency injection

NOT through repository imports.

---

# Root Structure

```
backend/
│
├── app/
├── tests/
├── alembic/
├── docs/
├── scripts/
├── docker/
│
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── README.md
└── alembic.ini
```

---

# app/

```
app/
│
├── core/
├── database/
├── modules/
├── shared/
├── main.py
└── __init__.py
```

---

# app/core

Contains global infrastructure.

```
core/

config.py
logging.py
exceptions.py
security.py (global utilities only)

dependencies.py

enums.py

constants.py

redis.py

cache.py
```

Rules

- Never import business modules here.
- Everything here must be reusable.

---

# app/database

```
database/

engine.py

session.py

base.py

mixins.py

types.py
```

Contains

- SQLAlchemy engine
- session management
- declarative base
- common mixins

No business logic.

---

# app/shared

Reusable helpers.

```
shared/

pagination.py

validators.py

utils.py

responses.py

storage.py
```

These helpers are domain-independent.

---

# app/modules

Every business domain lives here.

```
modules/

auth/

users/

vendors/

stalls/

menu/

orders/

payments/

notifications/

admin/

ai/

locations/

campus/
```

Each module is completely independent.

---

# Standard Module Layout

Every module follows this layout.

```
module/

router.py

service.py

repository.py

schemas.py

models.py

dependencies.py

exceptions.py

constants.py

utils.py

__init__.py
```

Not every file must exist immediately.

Create only when needed.

---

# Auth Module

```
auth/

router.py

service.py

repository.py

schemas.py

dependencies.py

security.py

exceptions.py

utils.py
```

Responsibilities

- registration

- login

- JWT

- authorization

- password hashing

Never owns User models.

User models belong to users module.

---

# Users Module

```
users/

models.py

repository.py

service.py

schemas.py
```

Owns

User

Student

Vendor

Admin

database models.

---

# Vendor Module

```
vendors/

router.py

service.py

repository.py

schemas.py

exceptions.py

dependencies.py
```

Responsibilities

Vendor profile

Vendor settings

Vendor verification

Vendor dashboard

Not authentication.

---

# Stall Module

```
stalls/

router.py

service.py

repository.py

schemas.py

models.py
```

Responsibilities

Food stalls

Operating hours

Availability

Locations

---

# Menu Module

```
menu/

router.py

service.py

repository.py

schemas.py
```

Responsibilities

Categories

Items

Pricing

Availability

Images

---

# Orders Module

```
orders/

router.py

service.py

repository.py

schemas.py
```

Responsibilities

Order lifecycle

Status

History

Cancellation

Pickup

---

# Payments Module

```
payments/

router.py

service.py

repository.py

schemas.py
```

Responsibilities

QR generation

Payment verification

Transactions

Refunds

---

# Notifications

```
notifications/

router.py

service.py

repository.py

schemas.py
```

Responsibilities

WhatsApp

Email

Push

SMS

---

# AI Module

```
ai/

router.py

service.py

repository.py

schemas.py

rag.py

embeddings.py

prompts.py
```

Responsibilities

LLM

Recommendations

Chatbot

Intent detection

RAG

Search

---

# Admin Module

```
admin/

router.py

service.py

repository.py

schemas.py
```

Responsibilities

Admin dashboard

Analytics

User management

Verification

Moderation

---

# Tests

Mirror production structure.

```
tests/

conftest.py

auth/

vendors/

stalls/

orders/

payments/

ai/

integration/

unit/
```

Example

```
tests/

auth/

test_login.py

test_register.py

test_security.py
```

Never place unrelated tests together.

---

# Docs

```
docs/

architecture/

database/

api/

deployment/

ai_context/
```

Contains

Architecture

ER diagrams

API docs

AI instructions

Design decisions

---

# Scripts

```
scripts/

seed_db.py

create_admin.py

reset_db.py

generate_openapi.py
```

Utility scripts only.

---

# Docker

```
docker/

postgres/

redis/

nginx/
```

Contains container-specific files.

---

# Import Rules

Allowed

```
router

↓

service

↓

repository

↓

database
```

Never

```
router

↓

repository
```

Never

```
repository

↓

service
```

Never

```
repository

↓

repository
```

across modules.

---

# Dependency Injection Rules

Routers receive services.

Services receive repositories.

Repositories receive AsyncSession.

Example

```
Router

↓

VendorService

↓

VendorRepository

↓

AsyncSession
```

---

# Circular Dependency Rule

Forbidden.

Instead use

- services

or

- shared utilities

or

- database models

Never import another module's repository.

---

# File Size Guidelines

router.py

< 300 lines

service.py

< 500 lines

repository.py

< 350 lines

schemas.py

< 350 lines

Split files if exceeded.

---

# Naming Convention

Routes

```
GET /vendors/me

PATCH /vendors/me

GET /vendors/{vendor_id}
```

Functions

```
get_vendor()

update_vendor()

create_vendor()
```

Repositories

```
get_by_id()

create()

update()

delete()
```

Schemas

```
VendorCreate

VendorUpdate

VendorResponse
```

Exceptions

```
VendorNotFoundError

InvalidVendorError
```

---

# Future Modules

Planned

```
reviews/

inventory/

coupons/

analytics/

recommendation/

search/

delivery/

kitchen/

queue/

loyalty/

chatbot/
```

These should follow the exact same module layout.

---

# Architecture Principle

Every module should be independently testable.

Every module should expose only its router.

Every module owns its business rules.

Business logic belongs only in services.

Database logic belongs only in repositories.

HTTP logic belongs only in routers.

Schemas validate data only.

Models represent persistence only.

This architecture must remain consistent for the lifetime of the project.