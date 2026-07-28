# CampusBite AI Backend
## 15_PATCH_WORKFLOW.md

Version: 1.0

Status: Canonical Development Workflow

---

# Purpose

This document defines **how every feature is developed** in the CampusBite AI Backend.

The project is intentionally built **patch-by-patch**, where each patch is a small, reviewable, independently testable unit of work.

This workflow exists to ensure

- stable development
- easier debugging
- better Git history
- easier code reviews
- easier AI-assisted development
- fewer merge conflicts
- consistent architecture

Every future module must follow this workflow.

---

# Development Philosophy

Never build an entire module in one step.

Instead, split it into logical patches.

Example

```
Vendor Module

↓

Patch 1

Patch 2

Patch 3

Patch 4

Patch 5
```

Each patch should

- compile
- pass tests
- be independently reviewable
- not break previous functionality

---

# Patch Size

A patch should be small enough that it can be reviewed in a few minutes.

Good

```
JWT Authentication

Vendor Profile

Booking Creation

Booking Cancellation
```

Bad

```
Entire Booking Module

Entire Vendor Module

Complete Payment System
```

---

# Patch Goals

Each patch should introduce one logical capability.

Examples

```
Authentication Foundation

↓

JWT utilities

Password hashing

Dependencies
```

Next patch

```
Registration

↓

Schemas

Repository

Service

Router
```

Next patch

```
Authorization

↓

Protected routes

Role dependencies

/me endpoint
```

---

# Standard Patch Order

Most modules should follow this order.

```
Patch 1

Project Foundation


Patch 2

Database Models


Patch 3

Schemas


Patch 4

Repository


Patch 5

Service


Patch 6

Router


Patch 7

Tests


Patch 8

Documentation
```

Small modules may combine some of these.

---

# What a Patch May Change

A patch should modify only the files necessary.

Example

```
schemas.py

service.py

router.py
```

Avoid changing unrelated modules.

---

# Preferred Patch Scope

Good

```
Vendor Profile Update

↓

schemas.py

service.py

router.py

tests
```

Bad

```
Vendor

+

Bookings

+

Payments

+

Notifications
```

---

# Patch Independence

Every patch should compile independently.

Do not create code that only works after three future patches.

---

# Compile After Every Patch

Before considering a patch complete, verify

- imports
- syntax
- formatting
- typing
- startup

Example

```
ruff check

ruff format

mypy

pytest
```

---

# Test Every Patch

Every patch should include

- unit tests
- regression tests (when applicable)

Never postpone testing until the end of the project.

---

# Git Workflow

One patch equals one commit.

Example

```
git commit

"Add vendor profile repository"

git commit

"Implement vendor profile service"

git commit

"Add vendor profile endpoints"
```

Avoid giant commits.

---

# Patch Documentation

Every patch should explain

- what changed
- why it changed
- files modified
- testing performed
- future work

---

# AI Development Workflow

When using an AI assistant

Always provide

- current architecture
- current patch
- previous completed patches
- coding standards
- module rules
- existing interfaces

Never ask an AI to redesign completed architecture unless explicitly desired.

---

# Patch Checklist

Before marking a patch complete

✓ Code compiles

✓ Ruff passes

✓ Imports are correct

✓ Type hints added

✓ Docstrings written

✓ Tests pass

✓ No duplicated logic

✓ Logging added where appropriate

✓ Exceptions handled

✓ No TODOs left behind unless intentional

---

# File Review Workflow

For every generated file

1.

Check imports

↓

2.

Check architecture

↓

3.

Check business logic

↓

4.

Check typing

↓

5.

Check documentation

↓

6.

Run tests

↓

7.

Commit

---

# Regression Policy

Whenever a bug is fixed

Add a regression test.

Never fix the same bug twice.

---

# Existing Code Rule

Before writing new code

Read

- service
- repository
- schemas
- models
- dependencies

Avoid duplicating existing functionality.

---

# When Refactoring

Refactor only if

- architecture improves
- readability improves
- duplication is removed
- performance significantly improves

Do not refactor working code unnecessarily.

---

# Breaking Changes

Avoid breaking existing APIs.

If unavoidable

- document them
- update tests
- update OpenAPI
- update clients

---

# Naming During Development

Maintain consistent naming.

Examples

```
VendorService

VendorRepository

VendorProfileResponse

VendorProfileUpdateRequest
```

Avoid inconsistent alternatives like

```
VendorSvc

VendorRepo

VendorDTO
```

---

# Documentation Requirements

Every completed patch should leave the project in a documented state.

Minimum documentation

- docstrings
- comments where necessary
- updated architecture docs if affected

---

# AI Code Review Checklist

Whenever an AI generates code, review

- imports
- architecture
- dependency direction
- SQLAlchemy usage
- FastAPI usage
- response models
- exception handling
- logging
- tests
- line lengths
- formatting

Never paste AI-generated code into the project without reviewing it.

---

# Testing Order

Preferred order

```
Unit Tests

↓

Router Tests

↓

Integration Tests

↓

Manual API Testing
```

---

# Large Features

Large features should be split.

Example

```
Bookings

↓

Patch 1

Models

↓

Patch 2

Repository

↓

Patch 3

Create Booking

↓

Patch 4

Cancel Booking

↓

Patch 5

Vendor Views

↓

Patch 6

Student Views

↓

Patch 7

Tests
```

---

# End-of-Patch Deliverables

A patch is complete only if it includes

- implementation
- documentation
- tests
- review
- commit

---

# Definition of Done

A patch is considered complete only when

- code compiles
- tests pass
- architecture rules are followed
- documentation is updated
- no obvious technical debt remains
- functionality works end-to-end

---

# Golden Rules

1. Develop in small patches.

2. One patch should introduce one capability.

3. Every patch must compile independently.

4. Every patch must include tests.

5. Commit after every completed patch.

6. Review AI-generated code before accepting it.

7. Add regression tests for every bug fix.

8. Never mix unrelated features into one patch.

9. Keep documentation synchronized with implementation.

10. Leave the codebase in a working state after every patch.

---

This document is the canonical development workflow for the CampusBite AI Backend.