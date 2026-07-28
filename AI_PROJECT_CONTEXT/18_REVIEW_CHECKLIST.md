# CampusBite AI Backend
## 18_REVIEW_CHECKLIST.md

Version: 1.0

Status: Canonical Code Review Checklist

---

# Purpose

This document defines the mandatory review process for every code change made to the CampusBite AI Backend.

Every pull request, patch, AI-generated contribution, and manual implementation must pass this checklist before being considered complete.

This checklist exists to ensure

- architectural consistency
- code quality
- maintainability
- correctness
- security
- production readiness

---

# Philosophy

The goal of code review is **not** to find fault.

The goal is to ensure that every new line of code integrates naturally into the existing project.

Every reviewer should ask:

> "Does this look like it belongs in this codebase?"

If the answer is no, the code should be revised.

---

# Stage 1 — Architecture Review

## Module Boundaries

Verify

- Router only contains HTTP concerns
- Service contains business logic
- Repository contains database access only
- Models contain ORM definitions
- Schemas contain Pydantic models
- Dependencies only provide dependency injection

Checklist

- [ ] Router contains no SQL
- [ ] Router contains no business logic
- [ ] Service contains no HTTPException
- [ ] Repository contains no business rules
- [ ] Repository contains no FastAPI imports
- [ ] Layering is preserved

---

## Dependency Direction

Allowed

```
Router
    ↓
Service
    ↓
Repository
```

Forbidden

```
Repository
    ↓
Service

Repository
    ↓
Repository (other module)

Service
    ↓
Router
```

Checklist

- [ ] No circular dependencies
- [ ] No cross-module repository imports
- [ ] Existing utilities reused

---

# Stage 2 — Coding Standards

## Formatting

Checklist

- [ ] Ruff passes
- [ ] Code is formatted
- [ ] Maximum line length ≤ 100
- [ ] Imports are organized
- [ ] No unused imports
- [ ] No unused variables

---

## Naming

Checklist

- [ ] Classes use PascalCase
- [ ] Functions use snake_case
- [ ] Constants use UPPER_CASE
- [ ] Variables are descriptive
- [ ] File names follow project conventions

---

## Type Hints

Checklist

- [ ] Every function has parameter types
- [ ] Every function has a return type
- [ ] Optional types are explicit
- [ ] Generic collections are typed

---

## Docstrings

Checklist

- [ ] Every public function has a docstring
- [ ] Complex logic is documented
- [ ] Arguments documented
- [ ] Return values documented
- [ ] Raised exceptions documented where appropriate

---

# Stage 3 — API Review

Checklist

- [ ] Correct HTTP method
- [ ] Correct endpoint path
- [ ] Uses response_model
- [ ] Uses request schemas
- [ ] Correct status codes
- [ ] OpenAPI summary present
- [ ] Endpoint naming follows REST

---

## Request Validation

Checklist

- [ ] Validation performed by Pydantic
- [ ] Business validation belongs in service
- [ ] No duplicated validation

---

## Response Models

Checklist

- [ ] ORM models are never returned directly
- [ ] Pydantic response models used
- [ ] model_validate() used where appropriate

---

# Stage 4 — Authentication & Authorization

Authentication

Checklist

- [ ] JWT handled through security.py
- [ ] Password hashing centralized
- [ ] No duplicate auth logic

Authorization

Checklist

- [ ] require_student used
- [ ] require_vendor used
- [ ] require_admin used
- [ ] No manual role comparisons

---

# Stage 5 — Database Review

Checklist

- [ ] SQLAlchemy 2.x API used
- [ ] AsyncSession used correctly
- [ ] Repository only performs queries
- [ ] Flush used where needed
- [ ] Refresh used where needed
- [ ] Transactions preserved

---

## Soft Delete

Checklist

- [ ] Soft-deleted rows excluded where appropriate
- [ ] deleted_at filters applied consistently

---

# Stage 6 — Business Logic Review

Checklist

- [ ] Logic belongs in service
- [ ] Repository remains simple
- [ ] Business rules are centralized
- [ ] Existing helpers reused
- [ ] No duplicated algorithms

---

# Stage 7 — Exception Review

Checklist

- [ ] Service raises custom exceptions
- [ ] Router translates exceptions
- [ ] HTTPException not raised outside router
- [ ] Error messages are consistent
- [ ] Error codes follow project conventions

---

# Stage 8 — Logging Review

Checklist

- [ ] Important actions logged
- [ ] Security events logged
- [ ] Sensitive data never logged
- [ ] Logging uses centralized logger

Never log

- passwords
- JWTs
- API keys
- secrets
- payment credentials

---

# Stage 9 — Testing Review

Checklist

- [ ] Unit tests added
- [ ] Router tests added
- [ ] Regression tests added if needed
- [ ] Existing tests still pass

---

## Regression Review

If a bug was fixed

Checklist

- [ ] Regression test added
- [ ] Previous behavior verified

---

# Stage 10 — Security Review

Checklist

- [ ] User input validated
- [ ] Authorization verified
- [ ] Authentication enforced
- [ ] Sensitive information hidden
- [ ] Generic authentication errors used
- [ ] No stack traces exposed

---

# Stage 11 — Performance Review

Checklist

- [ ] No unnecessary queries
- [ ] No duplicated database access
- [ ] Query complexity reasonable
- [ ] Pagination used where appropriate

---

# Stage 12 — Documentation Review

Checklist

- [ ] Docstrings updated
- [ ] Markdown docs updated if required
- [ ] API documentation accurate
- [ ] Architecture still documented correctly

---

# Stage 13 — AI Review

If the code was generated by an AI

Checklist

- [ ] Reviewed manually
- [ ] Existing project inspected first
- [ ] Existing utilities reused
- [ ] No hallucinated APIs
- [ ] No invented architecture
- [ ] No duplicated functionality

Never merge AI-generated code without review.

---

# Stage 14 — Patch Review

Checklist

- [ ] Patch is focused
- [ ] No unrelated files modified
- [ ] Patch compiles independently
- [ ] Backward compatibility preserved

---

# Stage 15 — Git Review

Checklist

- [ ] Commit message meaningful
- [ ] One feature per commit
- [ ] No debug code
- [ ] No commented-out code
- [ ] No temporary files

---

# Compile Checklist

Before merging

- [ ] Project starts successfully
- [ ] No syntax errors
- [ ] No import errors
- [ ] Ruff passes
- [ ] Type checking passes
- [ ] Tests pass

---

# Manual Testing Checklist

Verify

- [ ] Endpoint works
- [ ] Error responses correct
- [ ] Authentication works
- [ ] Authorization works
- [ ] Validation works
- [ ] Logging behaves correctly

---

# Pull Request Checklist

Before approving a PR

- [ ] Architecture preserved
- [ ] Code style followed
- [ ] Tests included
- [ ] Documentation updated
- [ ] No security issues
- [ ] No obvious performance regressions
- [ ] No duplicated logic

---

# Definition of Ready for Merge

A change is ready to merge only if

- it compiles successfully
- all automated tests pass
- manual verification is complete
- architecture remains consistent
- documentation is current
- no known critical issues remain

---

# Golden Rules

1. Preserve the existing architecture.
2. Review every AI-generated contribution manually.
3. Prefer consistency over cleverness.
4. Reject duplicated logic.
5. Never bypass the service layer.
6. Never bypass the repository layer.
7. Never expose ORM models directly.
8. Require tests for new functionality.
9. Keep documentation synchronized with implementation.
10. Leave the codebase cleaner than you found it.

---

This document is the canonical review checklist for all CampusBite AI Backend contributions.