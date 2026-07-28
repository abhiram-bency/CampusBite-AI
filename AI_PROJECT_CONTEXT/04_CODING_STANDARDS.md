# CampusBite AI Backend
## 04_CODING_STANDARDS.md

Version: 1.0

Status: Mandatory Development Standards

---

# Purpose

This document defines the coding standards for the entire CampusBite AI Backend.

Every AI assistant and every human contributor must follow these rules exactly.

The objective is to keep the entire codebase looking as if it were written by a single senior backend engineer.

---

# General Philosophy

Code should prioritize

- readability
- maintainability
- consistency
- explicitness
- correctness

Never optimize readability away for clever code.

---

# Python Version

Python

```
3.11+
```

Use modern Python syntax.

Examples

```python
str | None

list[str]

dict[str, int]
```

instead of

```python
Optional[str]

List[str]

Dict[str, int]
```

---

# Code Style

Formatter

```
Black
```

Import sorting

```
isort
```

Linter

```
Ruff
```

Type checking

```
mypy
```

All generated code must pass all four.

---

# Maximum Line Length

Maximum

```
88 characters
```

Never manually compress code just to fit.

Break arguments vertically.

Example

Good

```python
user = User(
    email=email,
    full_name=full_name,
    phone_number=phone_number,
)
```

Bad

```python
user = User(email=email, full_name=full_name, phone_number=phone_number)
```

---

# Imports

Standard library

↓

Third-party

↓

Local application imports

Example

```python
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.modules.users.models import User
```

Always separate groups with one blank line.

---

# __future__

Every file begins with

```python
from __future__ import annotations
```

---

# Docstrings

Every

- module
- class
- public function
- public method

must have a docstring.

Use Google-style or the project's existing hybrid style consistently.

Example

```python
def get_user(user_id: UUID) -> User:
    """Fetch a user by primary key.

    Args:
        user_id:
            User identifier.

    Returns:
        Matching user.
    """
```

---

# Comments

Comments explain

WHY

not

WHAT

Good

```python
# Avoid user enumeration attacks by returning
# the same error for unknown emails and wrong passwords.
```

Bad

```python
# Set variable to user
user = ...
```

---

# Naming Conventions

Variables

```
snake_case
```

Functions

```
snake_case
```

Methods

```
snake_case
```

Modules

```
snake_case.py
```

Classes

```
PascalCase
```

Constants

```
UPPER_CASE
```

Private members

```
_prefix
```

---

# Function Size

Prefer

20–40 lines

Maximum

~60 lines

If longer

Split into helper functions.

---

# Function Responsibility

One function

One responsibility.

Bad

```
Validate

Query DB

Hash password

Generate JWT

Return HTTP response
```

Good

```
Validate

↓

Repository

↓

Hash

↓

Issue token

↓

Router returns response
```

---

# Class Size

Prefer

under 300 lines.

Large services should be split.

---

# Type Hints

Everything should be typed.

Good

```python
def get_user(user_id: UUID) -> User | None:
```

Bad

```python
def get_user(user_id):
```

Avoid

```python
Any
```

unless absolutely necessary.

---

# Async Rules

Database

Always async.

Repositories

Always async.

Services

Async whenever calling repositories.

Never mix sync SQLAlchemy sessions.

---

# Exceptions

Never raise

```python
HTTPException
```

inside

Service

Repository

Security

Models

Only routers translate exceptions into HTTP responses.

---

# Logging

Use

```python
logger = get_logger(__name__)
```

Never use

```python
print()
```

Log

Unexpected situations

Errors

Warnings

Important business events

Do not log

Passwords

JWTs

Secrets

PII unnecessarily

---

# Dependency Injection

Always use FastAPI Depends.

Never instantiate services manually inside routes.

Good

```python
service: UserService = Depends(get_user_service)
```

Bad

```python
service = UserService(...)
```

---

# Repository Rules

Repositories

May

SELECT

INSERT

UPDATE

DELETE

flush()

refresh()

Repositories

Must not

Commit

Rollback

Issue JWTs

Hash passwords

Perform business validation

---

# Service Rules

Services

May

Validate

Authorize

Hash passwords

Issue tokens

Call repositories

Raise domain exceptions

Services

Must not

Import FastAPI

Return HTTP responses

Execute raw SQL

---

# Router Rules

Routers

May

Receive requests

Validate schemas

Call services

Return responses

Translate exceptions

Routers

Must not

Contain business logic

Contain SQL

Hash passwords

Generate JWTs directly

---

# Model Rules

Models represent persistence only.

Models should not contain

Business logic

HTTP logic

Validation

Authentication

Authorization

---

# Schema Rules

Pydantic schemas

Own request validation.

Examples

```
Email

Phone number

Password length

UUID parsing
```

Do not duplicate validation inside services unless it is business validation.

---

# Constants

Magic values should become constants.

Bad

```python
if len(password) < 8:
```

Good

```python
MIN_PASSWORD_LENGTH = 8
```

---

# Enums

Never compare raw strings.

Bad

```python
if user.role == "vendor":
```

Good

```python
if user.role == UserRoleEnum.VENDOR:
```

---

# String Formatting

Use

f-strings

Example

```python
f"User {user.id} authenticated"
```

Avoid

```python
"%s"

.format()
```

unless specifically required.

---

# Boolean Comparisons

Good

```python
if user.is_active:
```

Bad

```python
if user.is_active is True:
```

---

# None Checks

Good

```python
if user is None:
```

Bad

```python
if user == None:
```

---

# Collection Checks

Good

```python
if users:
```

Bad

```python
if len(users) > 0:
```

---

# SQLAlchemy Style

Use SQLAlchemy 2.x style.

Good

```python
stmt = select(User).where(User.id == user_id)
```

Avoid legacy Query API.

---

# Transactions

Never

```python
session.commit()
```

inside repositories.

One request

↓

One transaction

---

# Passwords

Always hash using

```
bcrypt
```

Never

Store plaintext

Log plaintext

Return hashes

---

# JWT

JWT creation belongs only in

```
security.py
```

Never duplicate token creation elsewhere.

---

# Circular Imports

Avoid them.

Prefer dependency inversion.

Repositories never import other repositories.

---

# File Organization

One major responsibility per file.

Examples

```
repository.py

service.py

router.py

schemas.py

exceptions.py

dependencies.py
```

Do not combine unrelated responsibilities.

---

# Testing

Every new feature should include tests.

Minimum

Repository tests

Service tests

Router tests

Regression tests when fixing bugs

---

# AI Code Generation Rules

AI assistants must

Match existing style.

Preserve architecture.

Never rewrite unrelated files.

Never introduce new abstractions unless necessary.

Never rename public APIs without instruction.

Never perform speculative refactoring.

---

# Documentation

Whenever adding

Endpoints

Services

Repositories

Schemas

Exceptions

Document them immediately.

Never leave undocumented public APIs.

---

# Performance

Prefer readable code first.

Optimize only when

Profiling demonstrates a bottleneck.

---

# Security

Never trust client input.

Always validate

Pydantic

↓

Business rules

↓

Database constraints

Never expose

Password hashes

Internal exceptions

Stack traces

JWT secrets

---

# Pull Request Checklist

Before considering code complete

✓ Ruff passes

✓ Black passes

✓ isort passes

✓ mypy passes

✓ Tests pass

✓ No duplicated logic

✓ Architecture preserved

✓ Docstrings added

✓ Public APIs documented

✓ No TODOs

✓ No debug prints

✓ No commented-out code

---

# Golden Rules

1. Readability over cleverness.

2. One layer, one responsibility.

3. Type everything.

4. Never duplicate logic.

5. Never bypass the service layer.

6. Repositories own SQL.

7. Routers own HTTP.

8. Services own business logic.

9. Security stays inside the auth module.

10. Every file should look like it was written by the same engineer.

This document is the canonical coding standard for the CampusBite AI Backend.