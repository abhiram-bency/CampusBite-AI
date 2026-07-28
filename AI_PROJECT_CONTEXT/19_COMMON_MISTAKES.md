# CampusBite AI Backend
## 19_COMMON_MISTAKES.md

Version: 1.0

Status: Common Development Mistakes & Anti-Patterns

---

# Purpose

This document records the most common mistakes encountered while developing the CampusBite AI Backend.

Every developer and AI assistant should review this file before implementing a new feature.

Avoiding these mistakes keeps the codebase

- maintainable
- consistent
- testable
- scalable
- easy to review

---

# Philosophy

The goal is not simply to write working code.

The goal is to write code that fits naturally into the existing architecture.

Many mistakes below still produce working software—but create technical debt.

Avoid them.

---

# Architecture Mistakes

## ❌ Putting Business Logic Inside Routers

Bad

```python
@router.post("/login")
async def login(payload):
    user = await session.execute(...)
    if verify_password(...):
        ...
```

Good

```text
Router

↓

Service

↓

Repository
```

Routers should only

- validate requests
- inject dependencies
- call services
- translate exceptions
- return responses

---

## ❌ Writing SQL Inside Services

Bad

```python
await session.execute(...)
```

inside

```
service.py
```

Good

Move database access into

```
repository.py
```

---

## ❌ Business Validation Inside Repository

Bad

```python
if email_exists():
    raise EmailAlreadyExistsException()
```

Repositories should never make business decisions.

They only answer questions.

Good

```python
return True
```

Service decides what that means.

---

## ❌ Importing Another Module's Repository

Bad

```python
VendorRepository

↓

AuthRepository
```

Never do this.

Instead

duplicate the required query inside the repository.

Repositories must remain independent.

---

## ❌ Circular Dependencies

Bad

```
Router

↓

Service

↓

Repository

↓

Service
```

Architecture must always flow downward.

---

# Authentication Mistakes

## ❌ Hashing Passwords Outside security.py

Never write

```python
bcrypt.hashpw(...)
```

outside

```
security.py
```

Always use

```python
hash_password()
```

---

## ❌ Creating JWTs Anywhere

JWT creation belongs only in

```
security.py
```

Use

```python
create_access_token()
```

---

## ❌ Decoding JWTs Manually

Never write

```python
jwt.decode(...)
```

inside routers or services.

Use

```python
decode_access_token()
```

---

## ❌ Comparing Roles Manually

Bad

```python
if user.role == "admin":
```

Good

```python
Depends(require_admin)
```

Always reuse authorization dependencies.

---

# Repository Mistakes

## ❌ Returning Dictionaries

Bad

```python
return {
    "id": user.id
}
```

Repositories should return ORM models.

---

## ❌ Returning HTTP Responses

Repositories must never know HTTP exists.

Never import

```
fastapi
```

inside repository.py.

---

## ❌ Committing Transactions

Repositories should

```
add()

flush()

refresh()
```

The request-scoped session owns commits.

---

## ❌ Performing Validation

Repositories should never validate

- passwords
- permissions
- business rules

---

# Service Mistakes

## ❌ Raising HTTPException

Bad

```python
raise HTTPException(...)
```

Good

```python
raise UserNotFoundError()
```

Router translates exceptions.

---

## ❌ Returning ORM Models Directly

Prefer response schemas.

Keep API representation separate from database representation.

---

## ❌ Logging Sensitive Information

Never log

- passwords
- JWTs
- tokens
- API keys
- payment information

---

# Router Mistakes

## ❌ Complex Logic

If an endpoint becomes longer than a few dozen lines,

the logic probably belongs inside the service.

---

## ❌ Returning ORM Models

Bad

```python
return user
```

Good

```python
return UserResponse.model_validate(user)
```

---

## ❌ Missing response_model

Every endpoint should define

```
response_model=
```

unless intentionally returning raw data.

---

# Schema Mistakes

## ❌ Duplicate Validation

Bad

```python
if len(password) < 8:
```

inside service.

Good

Use Pydantic

```python
Field(min_length=8)
```

---

## ❌ Returning Database Objects

Never expose SQLAlchemy models directly.

Always use response schemas.

---

## ❌ Mixing Request and Response Schemas

Create separate models.

Example

```
UserCreateRequest

UserResponse
```

---

# SQLAlchemy Mistakes

## ❌ Using Legacy Query API

Avoid

```python
session.query(...)
```

Use SQLAlchemy 2.x

```python
select(...)
```

---

## ❌ Forgetting Soft Delete Filters

If an entity supports soft deletion,

remember

```python
deleted_at.is_(None)
```

unless intentionally querying deleted rows.

---

## ❌ N+1 Queries

Avoid repeatedly querying inside loops.

Prefer eager loading where appropriate.

---

# Exception Mistakes

## ❌ Using Generic Exception

Avoid

```python
raise Exception(...)
```

Create project-specific exceptions.

---

## ❌ Leaking Internal Errors

Never expose

- SQL errors
- stack traces
- internal exception messages

to API clients.

---

# Logging Mistakes

## ❌ Missing Important Logs

Log

- registration
- login
- updates
- security failures
- important state changes

---

## ❌ Excessive Logging

Avoid logging every small internal operation.

Log meaningful events.

---

# Testing Mistakes

## ❌ No Regression Test

Whenever a bug is fixed,

add a regression test.

---

## ❌ Testing Only Happy Paths

Also test

- invalid input
- authorization
- authentication
- edge cases
- missing resources

---

## ❌ Testing the Wrong Layer

Repositories

↓

Database logic

Services

↓

Business logic

Routers

↓

HTTP behavior

Keep tests focused.

---

# AI Mistakes

## ❌ Rewriting Unrelated Files

Only modify files required for the task.

---

## ❌ Reinventing Existing Utilities

Before writing new code,

search the project.

Reuse existing

- exceptions
- utilities
- dependencies
- schemas
- helpers

---

## ❌ Hallucinating APIs

Never invent

```python
UserManager

AuthHelper

DatabaseManager
```

unless they already exist.

---

## ❌ Ignoring Existing Architecture

The project already has an architecture.

Extend it.

Do not redesign it.

---

# Documentation Mistakes

## ❌ Outdated Docstrings

Whenever code changes,

update documentation.

---

## ❌ Missing Type Hints

Every public function should be typed.

---

# Patch Mistakes

## ❌ Giant Patches

Bad

```
Entire Booking Module
```

Good

```
Booking Creation

Booking Cancellation

Booking Retrieval
```

---

## ❌ Mixing Features

One patch

↓

One capability.

---

# Git Mistakes

Avoid

```
"update"

"changes"

"fix"

"misc"
```

Prefer

```
Add vendor profile update endpoint

Implement JWT authorization dependency

Create booking repository
```

---

# Performance Mistakes

## ❌ Premature Optimization

Write readable code first.

Optimize only when profiling identifies bottlenecks.

---

## ❌ Duplicate Queries

If the same query appears repeatedly,

consider moving it into a reusable repository method.

---

# Security Mistakes

Never

- trust client input
- expose secrets
- log passwords
- compare roles manually
- bypass authentication
- bypass authorization

Always validate permissions.

---

# Code Review Mistakes

Do not approve code simply because it compiles.

Review

- architecture
- readability
- maintainability
- consistency
- testing
- documentation

---

# Before Every Commit

Ask yourself

- Does this belong in this layer?
- Am I duplicating existing code?
- Am I following project conventions?
- Have I added tests?
- Have I updated documentation?
- Could another developer understand this easily?

If any answer is "No", revise before committing.

---

# Golden Rules

1. Reuse existing code before writing new code.
2. Keep routers thin.
3. Keep repositories focused on database access.
4. Keep services responsible for business logic.
5. Never bypass project architecture.
6. Never expose ORM models directly.
7. Never raise `HTTPException` outside routers.
8. Never duplicate authentication or authorization logic.
9. Write tests for every feature and regression.
10. Leave the codebase cleaner than you found it.

---

This document serves as the canonical list of common mistakes and anti-patterns for the CampusBite AI Backend. Every contributor—human or AI—should use it as a final sanity check before submitting code.