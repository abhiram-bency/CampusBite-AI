# CampusBite AI Backend
# 99_PROJECT_STATE.md

Version: 1.0

Last Updated:
2026-07-28

Authoritative Project State

---

# IMPORTANT

This document is the **single source of truth** describing the
current implementation status of the CampusBite AI Backend.

Every AI assistant MUST read this file before writing any code.

If this file conflicts with another document,
THIS FILE WINS.

---

# Project Status

Current Milestone

Milestone 4

Current Phase

Vendor Module

Overall Completion

Approximately 18–22%

Backend Status

Production architecture established.

Core infrastructure complete.

Authentication complete.

Vendor module phase 1 complete.

Student module not yet started.

---

# Completed Infrastructure

## Core

✅ FastAPI

✅ Async SQLAlchemy

✅ PostgreSQL

✅ Alembic

✅ Redis

✅ Configuration

✅ Logging

✅ Exception Framework

✅ Health Endpoint

✅ Docker

✅ Docker Compose

---

# Authentication Module

Status

COMPLETE

Implemented

✅ Password hashing

✅ Password verification

✅ JWT creation

✅ JWT decoding

✅ Token validation

✅ Login

✅ Student Registration

✅ Vendor Registration

✅ Protected routes

✅ Current user dependency

✅ Role dependencies

Student

Vendor

Admin

Files

auth/

security.py

service.py

repository.py

router.py

schemas.py

dependencies.py

exceptions.py

---

Regression Fixes Applied

Removed

build_token_subject()

Removed

parse_token_subject()

Token subject now stores UUID directly.

TokenPayload uses

sub: str

Repository no longer depends on token helpers.

Repository matches frozen database schema.

Vendor registration updated to match Vendor ORM.

Router now contains

GET /auth/me

GET /auth/student-only

GET /auth/vendor-only

GET /auth/admin-only

Security.py is now the ONLY place using

passlib

python-jose

No module calls them directly.

---

# Vendor Module

Status

Phase 1 Complete

Implemented

Repository

Service

Router

Exceptions

Schemas

Dependencies

Endpoints

GET /vendors/me

PATCH /vendors/me

GET /vendors/{vendor_id}

Business Logic

View own profile

Update own profile

Admin lookup

Soft delete support

Regression Fixes

Repository does NOT import AuthRepository

save()

flush()

refresh()

Local get_user_by_id()

Business registration matches model

Verified fields match ORM

Soft delete respected

---

# Exception System

Implemented

Module specific exceptions

Central exception registration

Services never raise HTTPException

Routers translate module exceptions

---

# Logging

Implemented

Every module

logger = get_logger(__name__)

No print()

Structured logging

---

# Database

Current Tables

Users

Students

Vendors

Campuses

Locations

...

Current Transaction Pattern

Repositories

↓

Session.add()

↓

flush()

↓

refresh()

↓

request scoped commit

Repositories never commit.

Repositories never rollback.

---

# Testing

Current Status

Authentication tests updated.

Vendor tests updated.

Dependency override pattern adopted.

Conftest centralized.

Integration testing

NOT STARTED

---

# Coding Standards

Implemented

Python 3.11

Pydantic v2

SQLAlchemy 2

FastAPI

Type hints everywhere

Docstrings everywhere

Max line length

100

Google style docstrings

---

# Architecture Decisions

Module independence enforced.

Repository isolation enforced.

Services own business logic.

Routers own HTTP.

Repositories own SQL.

Authentication isolated.

Authorization dependency based.

Soft delete respected.

No cross-module repositories.

---

# Things That MUST NEVER Change

Security.py is the only JWT implementation.

Repositories never import repositories.

Routers never contain business logic.

Services never raise HTTPException.

Repositories never commit.

Module independence is mandatory.

Never duplicate helpers.

Reuse existing utilities.

Never redesign completed modules without good reason.

---

# Current Folder Status

Completed

core/

database/

auth/

vendors/

tests/

Infrastructure

Pending

students/

campuses/

stalls/

menus/

orders/

payments/

notifications/

ai/

analytics/

inventory/

---

# Next Module

Student Module

To Implement

Repository

Service

Router

Schemas

Exceptions

Dependencies

Tests

Endpoints

GET /students/me

PATCH /students/me

GET /students/{id}

Architecture

Must mirror Vendor module.

---

# Known Technical Debt

No refresh token support.

No rate limiting.

No media uploads.

No background workers.

No payment gateway.

No WhatsApp integration.

No recommendation engine.

No OpenTelemetry.

No metrics.

No caching.

These are intentionally postponed.

---

## Regression History

### 2026-07-28

Authentication

- Removed build_token_subject().
- Removed parse_token_subject().
- Simplified JWT payload to store UUID string directly.
- Removed obsolete TokenExpiredError usage.

Vendor Module

- Repository no longer imports AuthRepository.
- Added local get_user_by_id().
- save() now uses flush() + refresh().
- Repository updated to match latest Vendor ORM model.

Testing

- Rewrote auth tests to match current authentication implementation.
- Standardized dependency override pattern.

# AI Instructions

Before writing code

Read

AI_PROJECT_CONTEXT.md

Read

99_PROJECT_STATE.md

Verify architecture.

Reuse existing code.

Never recreate completed work.

Never replace completed modules.

Continue from the next unfinished roadmap item.

---

# Current Recommended Development Order

Student Module

↓

Campus Module

↓

Location Module

↓

Stall Module

↓

Menu Categories

↓

Menu Items

↓

Booking Module

↓

Order Lifecycle

↓

Payments

↓

Notifications

↓

WhatsApp

↓

AI

↓

Analytics

↓

Testing

↓

Production Hardening

---

# End of Project State

If an AI finishes implementing a feature,
THIS DOCUMENT MUST BE UPDATED
before starting the next feature.
