# CampusBite AI Backend
## 05_FASTAPI_GUIDE.md

Version: 1.0

Status: Framework Development Guide

---

# Purpose

This document defines how FastAPI must be used throughout the CampusBite AI Backend.

Every API endpoint, dependency, router, response model, exception, and middleware must follow these conventions.

The objective is to ensure every module behaves consistently regardless of who implements it.

---

# FastAPI Philosophy

FastAPI should only be responsible for

- HTTP request handling
- request validation
- dependency injection
- response serialization
- OpenAPI generation

Business logic belongs elsewhere.

The architecture is

```
Client
    │
    ▼
Router
    │
    ▼
Service
    │
    ▼
Repository
    │
    ▼
Database
```

---

# Project Structure

Every business module follows the same layout.

Example

```
users/

router.py
service.py
repository.py
schemas.py
models.py
dependencies.py
exceptions.py
```

No module should violate this structure.

---

# API Prefix

All endpoints live under

```
/api/v1
```

Example

```
/api/v1/auth/login

/api/v1/vendors/me

/api/v1/stalls

/api/v1/bookings
```

---

# Router Pattern

Each module owns exactly one router.

Example

```python
router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)
```

The main application includes routers.

Example

```python
app.include_router(
    vendors_router,
    prefix=settings.API_V1_PREFIX,
)
```

Routers must never include other routers.

---

# Endpoint Responsibilities

Endpoints should only

- accept requests
- validate schemas
- call services
- return responses
- translate exceptions

Endpoints must never

- write SQL
- hash passwords
- generate JWTs
- implement business rules

---

# HTTP Methods

GET

Read-only

POST

Create

PUT

Full replacement

PATCH

Partial update

DELETE

Delete resource

Never misuse methods.

---

# Request Validation

Always validate through Pydantic.

Example

```python
@router.post("/login")
async def login(
    payload: LoginRequest,
):
```

Never manually validate JSON.

---

# Response Models

Always specify response models.

Good

```python
@router.get(
    "/me",
    response_model=VendorProfileResponse,
)
```

Bad

```python
@router.get("/me")
```

---

# Status Codes

Use FastAPI status constants.

Example

```python
status.HTTP_201_CREATED
```

Never use raw numbers like

```
201
```

---

# Dependency Injection

Always inject dependencies.

Example

```python
service: VendorService = Depends(get_vendor_service)
```

Never instantiate manually.

Bad

```python
service = VendorService(...)
```

---

# Dependency Providers

Every service should have a dependency provider.

Example

```python
def get_vendor_service(
    session: AsyncSession = Depends(get_session),
) -> VendorService:
    repository = VendorRepository(session)
    return VendorService(repository)
```

---

# Authentication

Authentication uses

```
OAuth2PasswordBearer
```

Dependencies

```
get_current_user

require_student

require_vendor

require_admin
```

Protected endpoints should use

```python
Depends(require_vendor)
```

instead of checking roles manually.

---

# Authorization

Role validation belongs inside dependencies.

Example

```
require_admin()

↓

verify role

↓

return User
```

Endpoints never compare

```python
if current_user.role == ...
```

---

# Exception Handling

Services raise domain exceptions.

Example

```python
raise VendorProfileNotFoundError()
```

Routers translate them.

Example

```python
except VendorProfileNotFoundError as exc:
    raise HTTPException(...)
```

Global exceptions are registered once.

```
register_exception_handlers(app)
```

Never duplicate exception formatting.

---

# Response Serialization

Always return Pydantic models.

Example

```python
return VendorProfileResponse.model_validate(vendor)
```

Never return ORM objects directly.

---

# Async Endpoints

Every endpoint is async.

Example

```python
async def get_profile():
```

Never mix sync database code.

---

# Database Sessions

One request

↓

One AsyncSession

↓

One transaction

Repositories never create sessions.

Routers never create sessions.

---

# OpenAPI

Every endpoint should have

- summary
- response model
- status code

Example

```python
@router.get(
    "/me",
    summary="Get current vendor profile",
    response_model=VendorProfileResponse,
)
```

---

# Tags

Each router has exactly one tag.

Example

```
Authentication

Vendors

Bookings

AI

Admin
```

---

# Health Endpoints

Health endpoints return lightweight status.

Example

```
GET /health

GET /auth/health
```

Never execute expensive queries.

---

# Pagination

Collection endpoints should support

```
limit

offset
```

Future versions may migrate to cursor pagination.

---

# Query Parameters

Use explicit typing.

Example

```python
limit: int = Query(default=20, ge=1, le=100)
```

Never parse integers manually.

---

# Path Parameters

Always type them.

Good

```python
vendor_id: UUID
```

Bad

```python
vendor_id: str
```

---

# Request Bodies

Use schemas.

Good

```python
VendorProfileUpdateRequest
```

Bad

```python
dict
```

---

# Partial Updates

PATCH requests should use

```python
exclude_unset=True
```

Example

```python
updates = payload.model_dump(
    exclude_unset=True
)
```

Only supplied fields should change.

---

# File Uploads

Future modules may use

```
UploadFile
```

Never read entire files into memory unless necessary.

---

# Background Tasks

Use

```
BackgroundTasks
```

for

- emails
- notifications
- logging
- analytics

Never block API responses unnecessarily.

---

# Middleware

Middleware belongs in

```
main.py
```

Examples

- CORS
- request logging
- tracing
- rate limiting

Modules never register middleware.

---

# Lifespan

Startup

- configure logging
- verify PostgreSQL
- verify Redis

Shutdown

- close Redis
- dispose SQLAlchemy engine

Never initialize resources lazily if startup validation is available.

---

# Dependency Overrides

Tests should override dependencies.

Example

```python
app.dependency_overrides[
    get_vendor_service
] = fake_service
```

Never mock routers directly.

---

# Route Ordering

Literal routes must appear before parameterized routes.

Correct

```
/vendors/me

/vendors/{vendor_id}
```

Incorrect

```
/vendors/{vendor_id}

/vendors/me
```

Otherwise FastAPI may interpret

```
me
```

as

```
vendor_id
```

---

# API Versioning

Current version

```
v1
```

Future breaking changes should create

```
v2
```

Never silently break existing endpoints.

---

# Security Headers

Protected endpoints should return

```
WWW-Authenticate: Bearer
```

for authentication failures.

---

# CORS

Configured globally.

Origins come from

```
settings.cors_origins
```

Never hardcode origins.

---

# HTTP Status Guidelines

| Operation | Status |
|-----------|---------|
| GET | 200 |
| POST Create | 201 |
| PATCH | 200 |
| DELETE | 204 |
| Validation Error | 422 |
| Unauthorized | 401 |
| Forbidden | 403 |
| Not Found | 404 |
| Conflict | 409 |

---

# Testing Strategy

Every endpoint should have

- success test
- authentication test
- authorization test
- validation test
- regression test

Example

```
GET /vendors/me

✓ success

✓ unauthorized

✓ wrong role

✓ regression
```

---

# AI Development Rules

When generating FastAPI code

Always

- use dependency injection
- use async endpoints
- use response models
- use Pydantic validation
- preserve architecture

Never

- bypass services
- return ORM models
- duplicate validation
- raise HTTPException outside routers

---

# Golden Rules

1. Routers own HTTP.

2. Services own business logic.

3. Repositories own database access.

4. Dependencies own authentication and authorization.

5. Schemas own validation.

6. Middleware belongs only in the application entrypoint.

7. Every endpoint must be async.

8. Every endpoint must have a response model.

9. Every protected endpoint must use dependency injection.

10. FastAPI should never become the place where business logic lives.

This document is the canonical FastAPI development guide for the CampusBite AI Backend.