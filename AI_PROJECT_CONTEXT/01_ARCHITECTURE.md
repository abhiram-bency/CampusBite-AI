# 01_ARCHITECTURE.md

# CampusBite AI Backend

## Architecture & Engineering Standards

**Version:** 1.0
**Project:** CampusBite AI Backend
**Architecture:** Modular Monolith (Production-Grade)
**Framework:** FastAPI
**Language:** Python 3.11+

---

# 1. Architecture Philosophy

CampusBite AI follows a **Clean Architecture** inspired modular monolith.

The objective is:

* high maintainability
* clear module boundaries
* production scalability
* simple deployment
* future microservice migration

Every module is completely independent.

Examples:

* Auth
* Vendors
* Students
* Stalls
* Menu
* Bookings
* Payments
* Notifications
* AI
* Analytics

A module should never directly manipulate another module's database layer.

Instead it communicates through

* services
* dependencies
* shared abstractions

---

# 2. Overall Folder Structure

```text
app/

│
├── core/
│
├── database/
│
├── modules/
│
│   ├── auth/
│   ├── vendors/
│   ├── students/
│   ├── stalls/
│   ├── menu/
│   ├── bookings/
│   ├── payments/
│   ├── notifications/
│   ├── ai/
│   └── admin/
│
├── workers/
│
├── integrations/
│
├── utils/
│
└── main.py
```

Every module owns its complete implementation.

---

# 3. Module Structure

Every module follows exactly the same layout.

```text
module/

├── router.py
├── service.py
├── repository.py
├── schemas.py
├── models.py
├── dependencies.py
├── exceptions.py
└── utils.py
```

Optional:

```text
tests/
constants.py
validators.py
permissions.py
```

No unnecessary files.

---

# 4. Responsibility of Each Layer

## Router

Responsible only for:

* HTTP endpoints
* Request parsing
* Dependency Injection
* Returning responses
* Converting domain exceptions into HTTP errors

Never:

* SQL
* Password hashing
* Validation logic
* Authorization logic
* Business rules

Router should be extremely thin.

---

## Service

Responsible for business logic.

Examples:

* registration
* login
* booking workflow
* payment verification
* AI orchestration
* permissions
* validation

Service may call multiple repositories.

Service never imports FastAPI.

Never raise HTTPException.

Only raise domain exceptions.

---

## Repository

Responsible only for database access.

Allowed:

* SELECT
* INSERT
* UPDATE
* DELETE
* joins
* filters

Never:

* hashing
* validation
* business rules
* permission checks

Repository never imports FastAPI.

---

## Schemas

Contains only Pydantic models.

Examples:

Request schemas

Response schemas

Internal DTOs

Token payloads

Validation rules

No database code.

---

## Models

Contains SQLAlchemy ORM models.

No business logic.

---

## Dependencies

Responsible for:

* authentication
* authorization
* dependency injection
* request scoped services

---

## Exceptions

Every module owns its own exceptions.

No module raises HTTPException directly.

---

## Utils

Pure helper functions.

Examples:

date helpers

formatters

slug generators

etc.

---

# 5. Dependency Direction

Allowed

```text
Router

↓

Service

↓

Repository

↓

Database
```

Never

```text
Repository

↓

Service
```

Never

```text
Repository

↓

Repository
```

Never

```text
Router

↓

Repository
```

---

# 6. Authentication Architecture

JWT based authentication.

```
Router

↓

Dependency

↓

Security

↓

Service

↓

Repository
```

Security owns

* JWT
* bcrypt
* password hashing
* token validation

No other module touches JWT.

---

# 7. Authorization

Authorization happens through dependencies.

Examples

```
get_current_user()

require_student()

require_vendor()

require_admin()
```

Routes should never manually inspect roles.

Correct

```python
Depends(require_admin)
```

Wrong

```python
if current_user.role == ...
```

---

# 8. Database Transactions

Repositories never commit.

Repositories never rollback.

Repositories never control transactions.

They only stage changes.

Example

```
session.add()

session.flush()

session.refresh()
```

Commit happens once.

Request scoped session controls transaction lifetime.

---

# 9. Logging Strategy

Every module gets its own logger.

```python
logger = get_logger(__name__)
```

Log:

* important actions
* warnings
* failures
* unexpected states

Never log:

* passwords
* JWTs
* secrets
* API keys

---

# 10. Error Handling

Business layer raises domain exceptions.

Example

```
EmailAlreadyExistsException

VendorProfileNotFoundError

InvalidCredentialsException
```

Router converts them.

Example

```
HTTP 404

HTTP 409

HTTP 401

HTTP 403
```

Never mix both layers.

---

# 11. Validation

Validation order:

```
Pydantic

↓

Service

↓

Database
```

Example

Email format

↓

Business validation

↓

Unique constraint

Database should never be the first validator.

---

# 12. Dependency Injection

Dependencies create services.

Example

```python
get_vendor_service()

↓

VendorService()

↓

VendorRepository()
```

Routers never instantiate repositories.

---

# 13. Response Pattern

Successful response

```json
{
    "status": "success",
    "data": { }
}
```

Simple endpoints may return plain objects when appropriate.

Example

```
GET /auth/me
```

Validation errors use FastAPI defaults.

Business errors use project exception handlers.

---

# 14. Current Implemented Modules

Completed

* Core
* Database
* Configuration
* Logging
* Redis
* Exception System
* Authentication
* Vendor Profile (Phase 1)

In Progress

* Vendor Management

Upcoming

* Student Profile
* Stall Management
* Menu Management
* Booking Engine
* Order Lifecycle
* Payment Integration
* Notification Service
* WhatsApp Integration
* AI Chatbot
* Recommendation Engine
* Admin Dashboard APIs
* Analytics
* Search
* Inventory
* Reviews
* Coupons
* Reports

---

# 15. API Versioning

All APIs live under

```
/api/v1
```

Future

```
/api/v2
```

No breaking changes inside one version.

---

# 16. Testing Strategy

Three levels.

## Unit Tests

Mock repositories.

Test services.

---

## Router Tests

Dependency overrides.

No database.

Real FastAPI application.

---

## Integration Tests

Real PostgreSQL.

Real Redis.

End-to-end API testing.

---

# 17. Future Microservice Readiness

Every module should be capable of becoming its own service later.

Therefore:

* no circular imports
* no repository sharing
* no hidden dependencies
* no global mutable state

---

# 18. Performance Guidelines

Prefer:

* async everywhere
* pagination
* select only required columns
* avoid N+1 queries
* indexes for search columns

Never:

* unnecessary eager loading
* multiple commits
* duplicate queries

---

# 19. Security Principles

Always:

* hash passwords
* validate JWTs
* least privilege
* role-based authorization
* input validation
* parameterized SQL (ORM)

Never:

* trust client input
* expose stack traces
* log secrets
* hardcode credentials

---

# 20. Development Rules for AI Assistants

Any AI working on this repository **must** follow these rules:

1. Never violate module boundaries.
2. Never place business logic inside routers.
3. Never place SQL inside services.
4. Never commit inside repositories.
5. Never introduce circular imports.
6. Never bypass dependency injection.
7. Prefer modifying existing abstractions over creating duplicates.
8. Keep public APIs backward compatible unless explicitly instructed.
9. Preserve project style, typing, and docstring conventions.
10. If a requested change conflicts with these rules, explain the conflict before proposing an implementation.

---

# 21. Current Progress Snapshot

### ✅ Infrastructure

* FastAPI application bootstrap
* Configuration system
* Logging
* Database engine
* Redis integration
* Global exception handling
* Health endpoints

### ✅ Authentication

* JWT authentication
* Password hashing
* Registration
* Login
* Authorization dependencies
* Protected routes

### ✅ Vendor Module

* Repository
* Service
* Router
* Schemas
* Exceptions
* Profile APIs

### 🔄 Next Major Modules

1. Student Profile
2. Stall Management
3. Menu APIs
4. Booking Engine
5. Order Processing
6. Payment Gateway
7. Notification System
8. AI Chatbot
9. Admin APIs
10. Analytics

---

# Guiding Principle

> **The architecture prioritizes long-term maintainability over short-term convenience. Every feature should be implemented in a way that another engineer can understand, extend, and safely refactor years later without breaking unrelated modules.**
