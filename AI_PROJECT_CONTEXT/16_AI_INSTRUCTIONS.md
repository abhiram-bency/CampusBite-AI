# CampusBite AI Backend
## 16_AI_INSTRUCTIONS.md

Version: 1.0

Status: Canonical AI Development Instructions

---

# Purpose

This document contains the permanent instructions that every AI assistant
(Claude, ChatGPT, Gemini, Antigravity, Cursor, Windsurf, Copilot, etc.)
must follow while contributing to this repository.

This file exists to ensure that every AI produces code that is
architecturally consistent with the existing project.

These instructions override an AI's default coding style whenever they
conflict.

---

# Primary Objective

Your goal is **NOT** to generate code as quickly as possible.

Your goal is to produce code that

- matches the existing architecture
- follows every project convention
- minimizes future maintenance
- avoids technical debt
- is production-ready
- is reviewable
- is testable

---

# Never Assume

If something already exists,

DO NOT recreate it.

Always inspect the existing project first.

Examples

- existing exception hierarchy
- existing schemas
- existing repository methods
- existing dependencies
- existing utilities
- existing logging helpers
- existing configuration
- existing enums

Reuse existing code whenever possible.

---

# Always Read Before Writing

Before modifying any module, first inspect

```
models.py

schemas.py

repository.py

service.py

router.py

dependencies.py

exceptions.py
```

Never generate code blindly.

---

# Preserve Existing Architecture

Never redesign the architecture.

The project already follows

```
Router

↓

Service

↓

Repository

↓

Database
```

Maintain this structure.

Never bypass layers.

---

# Respect Module Independence

Modules must never depend directly on each other.

Allowed

```
Vendor Service

↓

Vendor Repository
```

Not allowed

```
Vendor Repository

↓

Auth Repository
```

If another module's data is required,

duplicate the required database query inside the repository.

Never import another repository.

---

# Router Rules

Routers should contain

- endpoints
- dependency injection
- response models
- exception translation

Routers must never contain

- SQL
- business logic
- password hashing
- validation logic
- authorization logic beyond dependency injection

---

# Service Rules

Services contain

- business rules
- validation
- orchestration
- logging
- repository composition

Services must never

- return HTTPException
- use SQLAlchemy directly
- construct SQL queries
- access FastAPI Request objects

---

# Repository Rules

Repositories perform only database access.

Repositories must

- execute SQLAlchemy queries
- return ORM models
- stage inserts
- flush when necessary

Repositories must never

- hash passwords
- validate business rules
- raise HTTP exceptions
- perform authorization

---

# Schema Rules

Every request and response uses Pydantic.

Never expose ORM models directly through the API.

Use

```
model_validate()

model_dump()

from_attributes=True
```

where appropriate.

---

# Exception Rules

Never raise HTTPException outside router.py.

Service layer raises custom exceptions.

Router translates them into HTTP responses.

---

# Logging Rules

Log

- important business events
- failures
- security events
- unexpected situations

Never log

- passwords
- JWTs
- API keys
- secrets
- database credentials

Use the project's centralized logger.

---

# Authentication Rules

JWT creation belongs only in

```
security.py
```

Password hashing belongs only in

```
security.py
```

Never duplicate hashing logic.

Never decode JWTs outside authentication utilities.

---

# Authorization Rules

Always reuse existing dependencies

```
get_current_user()

require_student()

require_vendor()

require_admin()
```

Never duplicate role checking.

---

# Database Rules

Use SQLAlchemy 2.x style.

Always

```
select()

session.execute()

scalar_one_or_none()

scalars()

flush()

refresh()
```

Avoid legacy Query API.

---

# Soft Delete Rules

Whenever reading business entities,

exclude soft-deleted rows unless explicitly required.

Prefer

```
deleted_at.is_(None)
```

when appropriate.

---

# Type Hint Rules

Every function must have

- parameter types
- return type

Never omit type hints.

---

# Docstring Rules

Every public function requires a docstring.

Include

- purpose
- arguments
- returns
- raises (if applicable)

Keep documentation synchronized with code.

---

# Validation Rules

Prefer Pydantic validation.

Avoid repeating validation inside services unless it is
business validation.

Examples

Schema validation

```
email format

phone format

string length
```

Business validation

```
duplicate email

duplicate registration number

vendor ownership

authorization
```

---

# API Rules

Use

```
response_model=
```

for every endpoint.

Return Pydantic models.

Never return ORM objects.

---

# Dependency Injection Rules

Always inject

```
services

repositories

database sessions
```

through FastAPI dependencies.

Avoid manual construction inside endpoints.

---

# Code Style

Follow

- Ruff
- Black-compatible formatting
- Python 3.11
- SQLAlchemy 2.x
- FastAPI best practices

Maximum line length

```
100 characters
```

---

# Naming Rules

Prefer descriptive names.

Good

```
VendorProfileResponse

VendorRepository

BookingService

StudentRegisterRequest
```

Avoid abbreviations.

---

# Testing Rules

Every new feature should include

- unit tests
- router tests
- regression tests (when appropriate)

Never leave a feature untested.

---

# Regression Policy

If a bug is fixed,

also add a regression test.

The same bug should never reappear.

---

# Documentation Rules

Whenever a public API changes,

update

- docstrings
- architecture docs
- related markdown documentation

---

# Performance Rules

Prefer readability over micro-optimizations.

Optimize only when profiling shows a real bottleneck.

Avoid premature optimization.

---

# Security Rules

Never

- trust user input
- expose stack traces
- leak authentication details
- leak database errors

Use generic authentication failure messages.

Always validate authorization.

---

# Existing Project Decisions

These architectural decisions are already finalized.

Do not change them unless explicitly instructed.

Examples

- JWT authentication
- Layered architecture
- SQLAlchemy ORM
- Async FastAPI
- Repository pattern
- Service pattern
- Soft delete
- Request-scoped sessions
- Centralized exception handling
- Structured logging

---

# AI Review Checklist

Before presenting code, verify

✓ Imports are correct

✓ Type hints exist

✓ Ruff formatting is respected

✓ Line length under 100

✓ No duplicated code

✓ Existing architecture preserved

✓ Existing utilities reused

✓ Existing exceptions reused

✓ Existing dependencies reused

✓ Correct response models

✓ Logging added where appropriate

✓ Tests updated if necessary

---

# When Unsure

If there are multiple possible implementations,

choose the one that

- introduces the fewest architectural changes
- reuses existing code
- minimizes future maintenance
- is most consistent with the existing repository

Do not invent new patterns if an existing one already solves the problem.

---

# Code Generation Workflow

Always follow this order

```
Understand Existing Code

↓

Identify Existing Utilities

↓

Design Minimal Change

↓

Implement

↓

Review

↓

Compile Check

↓

Type Check

↓

Test

↓

Return Final Code
```

---

# Forbidden Actions

Never

- rewrite unrelated files
- redesign the architecture
- duplicate repository logic
- duplicate authentication logic
- duplicate validation logic
- bypass services
- bypass repositories
- raise HTTPException outside routers
- expose ORM models directly
- commit placeholder code
- leave TODO comments instead of implementations

---

# Preferred AI Output

When generating code

1. Explain what changed.

2. Modify the smallest number of files possible.

3. Preserve backward compatibility.

4. Follow existing project conventions.

5. Produce production-ready code.

6. Ensure the code compiles.

7. Mention if tests should be updated.

---

# Golden Principle

The best contribution is the smallest correct contribution.

Favor consistency over cleverness.

Favor maintainability over brevity.

Favor existing architecture over new abstractions.

Every generated line of code should look like it was written by the original project author.