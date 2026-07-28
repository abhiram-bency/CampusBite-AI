# CampusBite AI Backend
## 14_API_DESIGN.md

Version: 1.0

Status: Canonical API Design Standards

---

# Purpose

This document defines the API design philosophy for the CampusBite AI Backend.

Every REST endpoint implemented in the project must follow these standards to ensure the API is

- predictable
- consistent
- scalable
- easy to consume
- well documented
- backward compatible

These rules apply to every module.

---

# API Philosophy

CampusBite follows REST principles.

The API should behave consistently regardless of module.

A developer should be able to predict an endpoint's behavior without reading its implementation.

---

# API Base URL

All endpoints are versioned.

```
/api/v1
```

Example

```
/api/v1/auth/login

/api/v1/vendors/me

/api/v1/bookings

/api/v1/stalls
```

Never expose unversioned endpoints.

---

# Versioning

Versioning occurs in the URL.

Example

```
/api/v1

/api/v2
```

Do not version using headers.

---

# Resource Naming

Resources use plural nouns.

Good

```
/vendors

/stalls

/bookings

/orders

/students
```

Bad

```
/getVendor

/vendorProfile

/createBooking
```

---

# HTTP Methods

Use the correct HTTP verb.

| Method | Purpose |
|----------|----------|
| GET | Read |
| POST | Create |
| PUT | Replace |
| PATCH | Partial Update |
| DELETE | Delete |

Never use GET to modify data.

---

# URL Design

URLs represent resources.

Good

```
GET /vendors/me

GET /vendors/{vendor_id}

PATCH /vendors/me

GET /stalls

GET /bookings/{booking_id}
```

Bad

```
/getVendor

/updateVendor

/deleteBooking
```

---

# Nesting

Only nest resources when ownership is clear.

Good

```
/stalls/{stall_id}/menu

/bookings/{booking_id}/items
```

Avoid deep nesting.

Bad

```
/campuses/1/stalls/2/bookings/5/items/9
```

---

# Request Body

Use JSON.

Example

```json
{
    "business_name": "Campus Cafe"
}
```

Never accept multiple request formats for the same endpoint.

---

# Response Body

Responses must always use response schemas.

Example

```json
{
    "id": "...",
    "business_name": "...",
    "created_at": "...",
    "updated_at": "..."
}
```

Avoid returning raw ORM models.

---

# Status Codes

Use standard HTTP status codes.

| Code | Meaning |
|------|----------|
|200|Success|
|201|Created|
|202|Accepted|
|204|No Content|
|400|Bad Request|
|401|Unauthorized|
|403|Forbidden|
|404|Not Found|
|409|Conflict|
|422|Validation Error|
|500|Internal Server Error|

Never return

```
200
```

for failures.

---

# Success Responses

Creation

```
201 Created
```

Update

```
200 OK
```

Delete

```
204 No Content
```

Read

```
200 OK
```

---

# Error Responses

Errors follow the centralized exception system.

Example

```json
{
    "error": {
        "code": "vendor_profile_not_found",
        "message": "Vendor profile not found.",
        "request_id": "...",
        "timestamp": "..."
    }
}
```

Never return plain strings.

Bad

```json
{
    "message":"Something went wrong"
}
```

---

# Validation Errors

Pydantic handles request validation.

Example

```
422 Unprocessable Entity
```

Never catch validation errors manually unless transforming them into the project's standardized error envelope.

---

# Authentication

Protected endpoints require

```
Authorization: Bearer <JWT>
```

Authentication is handled exclusively through dependencies.

Never parse JWTs inside routers.

---

# Authorization

Role restrictions use reusable dependencies.

Example

```
require_student

require_vendor

require_admin
```

Never compare roles manually inside endpoints.

---

# Query Parameters

Filtering belongs in query parameters.

Example

```
GET /stalls?campus_id=...

GET /bookings?status=pending

GET /vendors?page=2
```

---

# Pagination

Large collections must support pagination.

Future standard

```
?page=1

&page_size=20
```

Response

```json
{
    "items": [...],
    "page": 1,
    "page_size": 20,
    "total": 245,
    "pages": 13
}
```

Never return thousands of records in one response.

---

# Sorting

Sorting uses query parameters.

Example

```
?sort=name

?sort=-created_at
```

A leading minus indicates descending order.

---

# Filtering

Filters should be composable.

Example

```
GET /bookings

?status=confirmed

&campus_id=...

&vendor_id=...
```

Avoid creating separate endpoints for each filter combination.

---

# Searching

Search uses a dedicated query parameter.

Example

```
GET /stalls?search=coffee
```

Do not overload filter parameters for search.

---

# UUIDs

All primary resources are identified by UUIDs.

Example

```
GET /vendors/{vendor_id}
```

Avoid exposing database integer IDs.

---

# Date Format

Use ISO-8601 UTC timestamps.

Example

```
2026-07-28T09:15:30Z
```

Never use locale-specific date formats.

---

# Boolean Fields

Return booleans as JSON booleans.

Good

```json
{
    "verified": true
}
```

Bad

```json
{
    "verified":"Yes"
}
```

---

# Null Values

Return

```
null
```

for absent optional fields.

Do not use empty strings to represent missing values.

---

# PATCH vs PUT

PATCH updates only provided fields.

PUT replaces the entire resource.

CampusBite prefers PATCH for profile updates.

---

# DELETE

Successful deletes return

```
204 No Content
```

unless additional information is required.

---

# Idempotency

GET

PUT

DELETE

must be idempotent.

POST is not.

---

# OpenAPI Documentation

Every endpoint should include

- summary
- response model
- request model
- status code
- docstring

FastAPI generates OpenAPI automatically.

---

# Response Models

Always declare

```python
response_model=...
```

Example

```python
@router.get(
    "/me",
    response_model=VendorProfileResponse,
)
```

Never rely on implicit serialization.

---

# Dependency Injection

Use dependencies for

- authentication
- authorization
- services
- shared resources

Example

```python
Depends(get_vendor_service)

Depends(require_vendor)
```

---

# Business Logic

Routers should

- validate
- delegate
- return

Nothing else.

Business logic belongs in services.

---

# Consistency

Endpoints performing similar operations should return similar response shapes.

Example

```
POST /auth/login

POST /auth/register/student

POST /auth/register/vendor
```

All return

```json
{
    "access_token": "...",
    "token_type": "bearer",
    "user": { ... }
}
```

---

# Backward Compatibility

Never change

- response fields
- endpoint paths
- request formats

without introducing a new API version.

---

# Future Extensions

Future features

- Webhooks
- GraphQL
- AI streaming
- WebSockets

must still preserve these REST conventions where applicable.

---

# AI Development Rules

When generating endpoints

Always

- use REST conventions
- use response models
- use request models
- use dependency injection
- use proper status codes
- document endpoints
- return structured errors

Never

- return ORM models
- embed business logic in routers
- manually parse JWTs
- duplicate validation logic
- return inconsistent response shapes

---

# Golden Rules

1. Every endpoint begins with `/api/v1`.

2. Resources use plural nouns.

3. HTTP methods follow REST semantics.

4. Request and response bodies use Pydantic schemas.

5. Routers contain no business logic.

6. Protected endpoints use authentication dependencies.

7. Authorization uses role dependencies.

8. Errors use the centralized exception system.

9. Collections support pagination, filtering, and sorting.

10. API behavior should be predictable across every module.

---

This document is the canonical API design guide for the CampusBite AI Backend.