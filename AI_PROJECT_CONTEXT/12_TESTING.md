# CampusBite AI Backend
## 12_TESTING.md

Version: 1.0

Status: Canonical Testing Standards

---

# Purpose

This document defines the complete testing strategy for the CampusBite AI Backend.

Every module, feature, and future milestone must follow these testing rules to ensure:

- correctness
- maintainability
- confidence during refactoring
- regression prevention
- production reliability

Testing is treated as a first-class part of development—not an afterthought.

---

# Testing Philosophy

CampusBite follows the principle:

> **If it isn't tested, it isn't finished.**

Every new feature should include tests.

Bug fixes should include regression tests.

---

# Testing Pyramid

```
                 API Tests
             ----------------
            Integration Tests
        ------------------------
              Unit Tests
```

The majority of tests should be unit tests.

---

# Test Types

The backend uses four primary categories.

## 1. Unit Tests

Test a single function or class in isolation.

Examples:

- service methods
- utility functions
- validators
- security helpers

No database.

No HTTP server.

No Redis.

---

## 2. Router Tests

Test FastAPI endpoints.

These verify

- request validation
- dependency injection
- authentication
- authorization
- response models
- HTTP status codes

Dependencies are overridden using FastAPI's
`app.dependency_overrides`.

No real database.

---

## 3. Integration Tests

Integration tests verify that multiple layers work together.

Example

```
Router

↓

Service

↓

Repository

↓

Database
```

Uses a dedicated test database.

---

## 4. End-to-End Tests (Future)

Future browser/mobile/API testing.

Example

```
Client

↓

API

↓

Database

↓

Redis

↓

External Services
```

---

# Testing Stack

CampusBite uses

- pytest
- pytest-asyncio
- httpx.AsyncClient
- FastAPI dependency overrides

Future additions

- factory_boy
- Faker
- Testcontainers
- Playwright

---

# Project Structure

```
tests/

    conftest.py

    auth/

    vendors/

    bookings/

    stalls/

    admin/

    ai/

    integration/

    utils/
```

Every module has its own test directory.

---

# Naming Convention

Files

```
test_auth_router.py

test_vendor_service.py

test_security.py
```

Functions

```python
def test_login_returns_token():
```

Use descriptive names.

---

# Test Organization

Each production module should have matching tests.

Example

```
app/modules/auth/service.py

↓

tests/auth/test_service.py
```

---

# Fixtures

Reusable setup belongs in fixtures.

Examples

- AsyncClient
- fake users
- fake services
- sample payloads
- database sessions

Avoid duplicating setup code.

---

# Async Tests

Async code must use

```python
@pytest.mark.asyncio
```

or

```python
pytest_asyncio.fixture
```

Example

```python
@pytest.mark.asyncio
async def test_login():
    ...
```

---

# HTTP Testing

Use

```python
httpx.AsyncClient
```

with

```python
ASGITransport
```

Example

```python
transport = ASGITransport(app=app)

async with AsyncClient(
    transport=transport,
    base_url="http://test",
) as client:
    ...
```

Never start a real server during tests.

---

# Dependency Overrides

Router tests replace dependencies.

Example

```python
app.dependency_overrides[
    get_vendor_service
] = lambda: fake_service
```

This isolates the router.

---

# Mocking

Mock only external dependencies.

Good candidates

- Redis
- payment gateways
- AI APIs
- WhatsApp API
- email services

Avoid mocking internal business logic.

---

# Database Testing

Repository tests should eventually use a dedicated test database.

Never test against development or production databases.

Future setup

```
PostgreSQL

↓

Test Database

↓

Rollback After Test
```

---

# Authentication Tests

Verify

- password hashing
- password verification
- JWT creation
- JWT validation
- invalid tokens
- expired tokens
- missing tokens
- inactive users

---

# Authorization Tests

Verify

- student endpoints
- vendor endpoints
- admin endpoints
- forbidden access
- unauthenticated access

Every protected endpoint should have

- success test
- unauthorized test
- forbidden test

---

# Validation Tests

Verify

- missing fields
- invalid email
- invalid phone number
- invalid UUID
- invalid enum
- too-short strings
- too-long strings

Expected result

```
422
```

---

# Exception Tests

Verify custom exceptions produce

- correct status code
- correct error code
- correct message

Regression tests should exist for every custom exception.

---

# Repository Tests

Repository tests verify

- SQL queries
- inserts
- updates
- soft-delete filtering
- lookup correctness

Repositories should not contain business logic.

---

# Service Tests

Service tests verify

- business rules
- uniqueness checks
- validation
- state transitions
- logging side effects (where appropriate)

Repositories should be mocked.

---

# Router Tests

Router tests verify

- dependency injection
- HTTP status codes
- request validation
- response serialization
- authentication
- authorization

Services should be overridden.

---

# Utility Tests

Every helper function should have tests.

Examples

```
slugify()

normalize_email()

hash_password()

utcnow()
```

---

# Regression Tests

Every bug fixed should receive a regression test.

Example

```
Bug

↓

Fix

↓

Regression Test
```

The bug must never reappear unnoticed.

---

# Route Ordering Tests

FastAPI route ordering matters.

Example

```
/vendors/me

before

/vendors/{vendor_id}
```

Regression tests should verify

```
/vendors/me

returns

401

not

422
```

---

# Soft Delete Tests

Verify

- deleted rows are excluded
- active rows remain accessible

Repositories should consistently filter

```
deleted_at IS NULL
```

when appropriate.

---

# Logging Tests

Verify

- important events are logged
- correct log level
- no secrets logged

Do not compare entire log strings.

Prefer checking

- level
- message
- structured fields

---

# Performance Tests (Future)

Future benchmarks

- login latency
- booking creation
- AI inference
- search speed

These are separate from correctness tests.

---

# Coverage Goals

Target coverage

| Layer | Goal |
|--------|------|
| Utilities | 100% |
| Security | 100% |
| Services | 95%+ |
| Routers | 90%+ |
| Repositories | 90%+ |
| Overall | ≥90% |

Coverage is a guideline—not a substitute for good test quality.

---

# Test Isolation

Each test must be independent.

Never rely on

- execution order
- shared global state
- previous tests

A test should pass whether run alone or with the entire suite.

---

# Deterministic Tests

Tests should produce identical results every run.

Avoid

- random values (unless seeded)
- current time (unless frozen or controlled)
- network calls
- external APIs

---

# Time Handling

If testing timestamps

Prefer

- injected clocks
- helper functions
- fixed datetimes

Avoid relying on the current system time.

---

# AI Module Testing

Future AI modules should test

- prompt builders
- parsers
- caching
- fallback behavior
- token accounting
- response validation

Never depend on live AI providers during unit tests.

---

# Redis Testing

Mock Redis for unit tests.

Use a real Redis instance only in integration tests.

---

# External API Testing

Never call

- WhatsApp Cloud API
- payment gateways
- email providers

during unit tests.

Mock them.

---

# CI Requirements

Every pull request should run

- linting
- formatting
- type checking
- all tests

A failed test blocks merging.

---

# Code Review Expectations

Every feature should include

- production code
- matching tests
- regression tests (if fixing a bug)

Missing tests should be treated as incomplete work.

---

# AI Development Rules

When generating tests

Always

- write readable tests
- test behavior, not implementation
- isolate dependencies
- use fixtures
- keep one logical assertion group per test
- write descriptive test names

Never

- duplicate production logic
- depend on test execution order
- use real external services
- hardcode fragile timing assumptions
- skip tests without a documented reason

---

# Golden Rules

1. Every feature must include tests.

2. Unit tests should outnumber integration tests.

3. Routers are tested using dependency overrides.

4. Services are tested with mocked repositories.

5. Repositories are tested against a test database.

6. Every bug fix must include a regression test.

7. Tests must be deterministic and isolated.

8. Never call external services during unit tests.

9. Protect authentication and authorization with dedicated tests.

10. Testing is part of development—not something done afterward.

---

This document is the canonical testing guide for the CampusBite AI Backend.