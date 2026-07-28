# CampusBite AI Backend
## 09_AUTHORIZATION.md

Version: 1.0

Status: Authorization & Access Control Guide

---

# Purpose

This document defines how authorization works throughout the CampusBite AI Backend.

Authentication answers

> **Who are you?**

Authorization answers

> **What are you allowed to do?**

Every protected API in the project must follow this document.

---

# Authorization Philosophy

CampusBite follows

```
Authentication

↓

Authorization

↓

Business Logic

↓

Database
```

Authorization always happens **before** business logic.

A request that is not authorized must never reach the service layer.

---

# Access Control Model

CampusBite uses

```
Role-Based Access Control (RBAC)
```

The authenticated user's role determines which APIs they may access.

---

# User Roles

Current roles

```
Student

Vendor

Admin
```

Stored as

```
UserRoleEnum
```

Never compare raw strings.

Good

```python
if user.role == UserRoleEnum.ADMIN:
```

Bad

```python
if user.role == "admin":
```

---

# Authorization Pipeline

```
HTTP Request

↓

JWT

↓

decode_access_token()

↓

Current User

↓

Role Verification

↓

Business Logic

↓

Database
```

---

# Authorization Dependencies

The project exposes reusable dependencies.

```
get_current_user()

↓

require_student()

↓

require_vendor()

↓

require_admin()
```

These are the **only** supported authorization entry points.

---

# Dependency Responsibilities

## get_current_user()

Responsibilities

- validate bearer token
- decode JWT
- load user
- verify active account
- return User

No role verification.

---

## require_student()

Responsibilities

- call get_current_user()
- verify role == STUDENT
- return User

---

## require_vendor()

Responsibilities

- call get_current_user()
- verify role == VENDOR
- return User

---

## require_admin()

Responsibilities

- call get_current_user()
- verify role == ADMIN
- return User

---

# Router Usage

Student endpoint

```python
@router.get("/bookings")
async def get_bookings(
    current_user: User = Depends(require_student),
):
    ...
```

Vendor endpoint

```python
current_user: User = Depends(require_vendor)
```

Admin endpoint

```python
current_user: User = Depends(require_admin)
```

Authenticated endpoint

```python
current_user: User = Depends(get_current_user)
```

---

# Never Perform Manual Authorization

Do not write

```python
if current_user.role != UserRoleEnum.ADMIN:
    raise HTTPException(...)
```

inside routes.

Instead

```python
Depends(require_admin)
```

---

# Service Layer Rules

Services assume authorization has already succeeded.

Good

```
Router

↓

Authorization

↓

Service
```

Bad

```
Router

↓

Service

↓

Role Checks
```

Services should not repeatedly verify roles.

---

# Repository Rules

Repositories know nothing about authorization.

Repositories

- query
- insert
- update
- delete

Repositories never know

- JWT
- roles
- permissions
- users
- FastAPI

---

# Authorization Hierarchy

```
Admin

↓

Vendor

↓

Student
```

Current implementation treats these as separate roles.

Admin does **not** automatically inherit vendor APIs unless explicitly allowed.

---

# Protected Endpoints

Examples

```
GET /auth/me

↓

Authenticated User
```

```
GET /vendors/me

↓

Vendor
```

```
PATCH /vendors/me

↓

Vendor
```

```
GET /vendors/{vendor_id}

↓

Admin
```

```
POST /bookings

↓

Student
```

---

# Public Endpoints

Examples

```
GET /health

GET /auth/health

POST /auth/login

POST /auth/register/student

POST /auth/register/vendor
```

These require no authentication.

---

# Authorization Decisions

Authorization should answer only

```
Can this role access this endpoint?
```

It should **not** answer

```
Does this record exist?

Is this booking paid?

Does this stall belong to the vendor?
```

Those are business rules.

---

# Ownership Validation

Ownership checks belong inside services.

Example

```
Vendor

↓

Update Stall

↓

Verify stall.owner == current_vendor

↓

Update
```

This is **not** role authorization.

It is business validation.

---

# Current User Object

Dependencies return

```python
User
```

Services receive

```python
current_user: User
```

Never decode JWT twice.

Never reload the user unnecessarily.

---

# Authorization Errors

Current project exceptions

```
InvalidTokenException

InactiveUserException

InsufficientPermissionsException
```

Services and dependencies raise module exceptions.

Routers translate them into HTTP responses.

---

# HTTP Status Codes

Invalid JWT

```
401 Unauthorized
```

Inactive account

```
403 Forbidden
```

Wrong role

```
403 Forbidden
```

Missing resource

```
404 Not Found
```

---

# Principle of Least Privilege

Every endpoint should request only the minimum permission required.

Good

```
Vendor endpoint

↓

require_vendor
```

Bad

```
Authenticated endpoint

↓

Manual role checking
```

---

# Business Ownership

Example

Vendor edits own profile

```
require_vendor()

↓

current_user.id

↓

service.update_profile()
```

Admin views vendor

```
require_admin()

↓

service.get_vendor_profile()
```

Different permissions.

Different business logic.

---

# Future Permission Model

Current implementation

```
Role Based
```

Future implementation may support

```
Permission Based
```

Example

```
Vendor

↓

manage_menu

↓

manage_orders

↓

manage_stalls
```

or

```
Admin

↓

view_reports

↓

manage_users

↓

verify_vendor
```

This can coexist with RBAC.

---

# Resource-Level Authorization

Future modules should verify ownership.

Example

```
Vendor

↓

PATCH /stalls/{stall_id}

↓

Load Stall

↓

stall.vendor_id == current_user.id

↓

Update
```

This belongs in services.

---

# Multi-Tenant Authorization

CampusBite supports multiple campuses.

Future authorization may enforce

```
Admin

↓

Campus A

↓

Cannot manage Campus B
```

This will use

```
campus_id
```

rather than only roles.

---

# JWT Role Trust

The JWT contains

```
role
```

for convenience.

However, the backend always loads the current User from the database.

The database remains the source of truth.

If a user's role changes after token issuance, future requests should rely on the current database record, not solely on the token claim.

---

# Authorization Testing

Tests should verify

- missing token
- invalid token
- expired token
- inactive user
- student denied vendor route
- vendor denied admin route
- admin allowed admin route
- authenticated user access
- protected routes
- dependency wiring

---

# AI Development Rules

When generating authorization code

Always

- use Depends()
- use reusable dependencies
- keep routers thin
- perform role checks in dependencies
- perform ownership checks in services

Never

- decode JWT in routers
- compare raw role strings
- duplicate authorization logic
- query repositories directly from routers
- raise HTTPException inside services

---

# Future Authorization Features

Planned roadmap

- Fine-grained permissions
- Campus-level administration
- Vendor verification workflow
- Menu management permissions
- Order management permissions
- Audit logging
- Permission caching
- Temporary privilege elevation
- Super Admin role
- API scopes
- OAuth scopes

---

# Golden Rules

1. Authentication identifies the user.

2. Authorization determines access.

3. Every protected endpoint must use dependency injection.

4. Services trust authorized users.

5. Repositories know nothing about authorization.

6. Never duplicate role checks.

7. Use `UserRoleEnum` everywhere.

8. Ownership validation belongs in services.

9. Authorization must happen before business logic.

10. Keep authorization centralized, reusable, and testable.

This document is the canonical authorization guide for the CampusBite AI Backend.