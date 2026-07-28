# AI_PROJECT_CONTEXT.md

# CampusBite AI Backend
## Complete AI Development Context

Version: 1.0

This file is the permanent context for every AI assistant working on this project.

Every future code generation, review, refactoring, testing, documentation,
or architecture decision must follow this document.

--------------------------------------------------------------------

# PROJECT

CampusBite AI

AI-powered WhatsApp based food pre-ordering platform for universities.

Backend Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 Async
- Alembic
- Redis
- Pydantic v2
- JWT Authentication
- Docker
- GitHub Actions
- Python 3.11

--------------------------------------------------------------------

# PRIMARY GOAL

Build a production-quality backend.

NOT a tutorial.

NOT a college project.

Everything should look like it belongs inside a real startup.

--------------------------------------------------------------------

# DEVELOPMENT PHILOSOPHY

Always prioritize

Architecture
>

Readability
>

Maintainability
>

Performance

over writing the shortest code.

--------------------------------------------------------------------

# PROJECT STATUS

Completed

✓ Core Infrastructure

✓ Logging

✓ Config

✓ Database

✓ Redis

✓ Authentication

✓ Authorization

✓ Vendor Module Phase 1

Currently Working On

Next module after Vendor.

Future modules remain listed below.

--------------------------------------------------------------------

# MODULE INDEPENDENCE RULE

Every module must be independent.

Example

Vendor Module

owns

repository

service

router

schemas

exceptions

dependencies

The Vendor module must NEVER import another module's repository.

Allowed

Vendor Service
↓

Vendor Repository

Forbidden

Vendor Repository
↓

Auth Repository

--------------------------------------------------------------------

# LAYER RULES

Router

Only

Validation

Dependency Injection

HTTP

Response Models

Never

Business Logic

Never SQL

Never Password Verification

Never Authorization Decisions

--------------------------------------------------------------------

Service

Business Logic

Validation

Workflows

Authorization Decisions

Repository Coordination

Can call multiple repositories.

Never HTTPException.

--------------------------------------------------------------------

Repository

Database only.

SQLAlchemy only.

No business rules.

No validation.

No authentication.

--------------------------------------------------------------------

Schemas

Pydantic only.

No ORM queries.

No business logic.

--------------------------------------------------------------------

Models

SQLAlchemy ORM only.

--------------------------------------------------------------------

# AUTHENTICATION

Uses JWT.

Password hashing uses bcrypt.

JWT utilities live only inside

app/modules/auth/security.py

Never call jose directly outside security.py.

Never call passlib outside security.py.

--------------------------------------------------------------------

# AUTHORIZATION

Uses dependency injection.

Examples

require_student

require_vendor

require_admin

Role checks belong ONLY inside dependencies.py

Never duplicate role logic elsewhere.

--------------------------------------------------------------------

# EXCEPTION SYSTEM

Every module owns its own exceptions.

Never raise HTTPException inside services.

Raise module exceptions.

Router translates module exceptions into HTTP.

--------------------------------------------------------------------

# LOGGING

Every module

logger = get_logger(__name__)

No print()

Use structured logging.

Log

unexpected situations

important updates

security events

Do NOT log passwords

Do NOT log tokens

Do NOT log secrets

--------------------------------------------------------------------

# DATABASE

Async SQLAlchemy.

Session injected per request.

Repositories never commit.

Repositories never rollback.

Repositories only

add()

flush()

refresh()

Commit happens once after request.

--------------------------------------------------------------------

# SOFT DELETE

Every query excluding deleted rows must explicitly check

deleted_at IS NULL

unless intentionally including deleted rows.

--------------------------------------------------------------------

# TESTING

Every module should eventually have

repository tests

service tests

router tests

Current testing uses

httpx

pytest

dependency_overrides

No real database unless integration tests.

--------------------------------------------------------------------

# CODING STYLE

Python 3.11

Pydantic v2

SQLAlchemy 2.0

Type hints everywhere.

Return types everywhere.

Docstrings everywhere.

No wildcard imports.

Maximum line length

100

--------------------------------------------------------------------

# DOCSTRINGS

Every public function

Google style.

Explain

Args

Returns

Raises

Avoid useless comments.

Explain WHY.

--------------------------------------------------------------------

# PATCH DEVELOPMENT

Every feature is developed in patches.

Each patch must

compile

pass Ruff

pass formatting

integrate with previous patches

never break architecture

--------------------------------------------------------------------

# REVIEW RULES

Whenever modifying existing code

First understand

architecture

dependencies

existing style

Only then write code.

Prefer improving existing code

instead of rewriting entire modules.

--------------------------------------------------------------------

# AI RULES

Never generate code first.

Always inspect surrounding code.

Match existing naming.

Match existing architecture.

Reuse existing helpers.

Never duplicate utilities.

Never introduce alternative implementations.

If helper exists

reuse it.

If schema exists

reuse it.

If dependency exists

reuse it.

If exception exists

reuse it.

--------------------------------------------------------------------

# WHEN REVIEWING CODE

Look for

Architecture violations

Business logic inside router

SQL inside service

HTTPException inside service

Repository importing another repository

Duplicate code

Naming consistency

Missing typing

Missing docstrings

Soft delete bugs

Authentication bugs

Authorization bugs

Logging mistakes

Transaction mistakes

--------------------------------------------------------------------

# WHEN ADDING FEATURES

Never create unnecessary files.

Never create unnecessary abstractions.

Keep architecture flat.

If existing file naturally owns the code

extend it.

--------------------------------------------------------------------

# CURRENT IMPLEMENTED MODULES

Core

Database

Redis

Authentication

Authorization

Vendor

--------------------------------------------------------------------

# FUTURE MODULES

Student

Campus

Locations

Stalls

Menu Categories

Menu Items

Orders

Bookings

Payments

Notifications

WhatsApp Integration

AI Recommendation Engine

Admin Dashboard

Analytics

Reviews

Coupons

Offers

Inventory

Image Uploads

Background Workers

Search

--------------------------------------------------------------------

# FUTURE INFRASTRUCTURE

Rate Limiting

Caching

OpenTelemetry

Metrics

Health Monitoring

Audit Logs

Background Scheduling

CI/CD Improvements

Load Testing

Distributed Deployment

--------------------------------------------------------------------

# BEFORE WRITING ANY CODE

AI must ask itself

1

Does this already exist?

2

Can existing helper be reused?

3

Which module owns this responsibility?

4

Am I breaking module independence?

5

Is business logic leaking into router?

6

Am I creating duplicate code?

7

Does this match the project's architecture?

If any answer is wrong

fix architecture first.

--------------------------------------------------------------------

# FINAL OBJECTIVE

The finished backend should resemble a professionally engineered FastAPI
production codebase suitable for deployment, open-source publication,
and recruiter portfolio review.

Maintain consistency above all else.

Every new patch must make the codebase better—not merely larger.
