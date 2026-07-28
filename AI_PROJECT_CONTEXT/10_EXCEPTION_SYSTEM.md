# CampusBite AI Backend
## 10_EXCEPTION_SYSTEM.md

Version: 1.0

Status: Global Exception Handling Guide

---

# Purpose

This document defines the complete exception handling architecture used throughout the CampusBite AI Backend.

Every module must follow these standards so that errors are

- predictable
- consistent
- debuggable
- user-friendly
- machine-readable

The backend must never expose internal stack traces or database errors to API clients.

---

# Exception Philosophy

CampusBite follows a layered exception architecture.

```
Repository

↓

Service

↓

Router

↓

Global Exception Handler

↓

HTTP Response
```

Each layer has a clearly defined responsibility.

---

# Goals

The exception system should

- separate business errors from framework errors
- produce identical response formats
- support logging
- simplify debugging
- simplify frontend integration
- support future internationalization

---

# Exception Hierarchy

```
Exception

↓

CampusBiteError

↓

ValidationError

AuthenticationError

AuthorizationError

ConflictError

NotFoundError

BusinessRuleError

↓

Module-specific exceptions
```

---

# Base Exception

Every custom exception must inherit from

```python
CampusBiteError
```

The base exception contains

```
message

error_code

status_code

details
```

---

# Exception Flow

```
Database Error

↓

Repository

↓

Service Exception

↓

Router

↓

Global Handler

↓

JSON Response
```

Repositories should never decide HTTP responses.

---

# Layer Responsibilities

## Repository

Repositories may raise

- SQLAlchemy exceptions
- database connectivity errors

Repositories should not raise

- HTTPException
- business exceptions
- authentication exceptions

---

## Service

Services own business validation.

Services raise

- EmailAlreadyExistsException
- InvalidCredentialsException
- VendorProfileNotFoundError
- BookingConflictException

Services never raise

```python
HTTPException
```

---

## Router

Routers

- call services
- catch service exceptions
- convert exceptions when necessary
- return response models

Routers should remain lightweight.

---

## Global Exception Handler

The global exception handler is responsible for

- formatting responses
- logging
- masking internal errors
- mapping exception classes to HTTP status codes

---

# Exception Categories

## Validation

Examples

```
Invalid request

Missing field

Invalid UUID

Regex mismatch
```

Handled automatically by FastAPI/Pydantic.

---

## Authentication

Examples

```
Invalid token

Expired token

Inactive user

Invalid credentials
```

---

## Authorization

Examples

```
Wrong role

Permission denied

Access forbidden
```

---

## Conflict

Examples

```
Email already exists

Registration number exists

Duplicate booking

Duplicate menu item
```

---

## Not Found

Examples

```
Vendor not found

Booking not found

Menu item not found

Campus not found
```

---

## Business Rules

Examples

```
Booking already completed

Order already cancelled

Vendor already verified

Payment already processed
```

---

# Current Authentication Exceptions

```
AuthError

↓

InvalidTokenException

InactiveUserException

InvalidCredentialsException

EmailAlreadyExistsException

RegistrationNumberAlreadyExistsException

InsufficientPermissionsException
```

---

# Current Vendor Exceptions

```
VendorProfileNotFoundError
```

---

# Naming Convention

Good

```
BookingNotFoundError

MenuItemConflictError

VendorAlreadyVerifiedError

OrderAlreadyCompletedError
```

Bad

```
BookingError

MenuError

VendorIssue

ProblemException
```

---

# Exception Messages

Messages should be

- short
- user friendly
- non-technical

Good

```
Invalid email or password.
```

Bad

```
bcrypt verification failed.
```

---

# Error Codes

Every exception should expose

```
error_code
```

Example

```
invalid_token

inactive_user

email_exists

vendor_not_found
```

These codes remain stable even if messages change.

---

# HTTP Status Mapping

| Exception | HTTP Status |
|------------|------------|
| Validation | 422 |
| Authentication | 401 |
| Authorization | 403 |
| Not Found | 404 |
| Conflict | 409 |
| Business Rule | 400 |
| Unexpected | 500 |

---

# Standard Response Format

Every error response should follow the same structure.

```json
{
    "error": {
        "code": "vendor_profile_not_found",
        "message": "Vendor profile not found."
    }
}
```

Optional metadata

```json
{
    "error": {
        "code": "...",
        "message": "...",
        "details": {
            ...
        }
    }
}
```

---

# Internal Errors

Unexpected exceptions should never expose

- SQL queries
- stack traces
- filesystem paths
- environment variables
- secrets

Clients should receive

```json
{
    "error": {
        "code": "internal_server_error",
        "message": "An unexpected error occurred."
    }
}
```

---

# Logging

Every exception should be logged.

Logging levels

```
INFO

↓

WARNING

↓

ERROR

↓

CRITICAL
```

---

## INFO

Examples

```
Duplicate login attempt

Vendor profile updated

User logout
```

---

## WARNING

Examples

```
Invalid credentials

Permission denied

Inactive account
```

---

## ERROR

Examples

```
Database unavailable

Redis unavailable

Unexpected exception
```

---

## CRITICAL

Examples

```
Application startup failure

Configuration corruption

Security breach
```

---

# What Should Be Logged

Log

- request path
- HTTP method
- authenticated user ID
- error code
- exception message
- timestamp

Never log

- passwords
- JWT secrets
- access tokens
- password hashes
- payment information

---

# SQLAlchemy Exceptions

Repositories may receive

```
IntegrityError

OperationalError

DBAPIError
```

Services should translate these into business exceptions whenever appropriate.

Example

```
IntegrityError

↓

EmailAlreadyExistsException
```

---

# Validation Errors

Handled automatically by FastAPI.

Never duplicate validation manually.

Good

```python
email: EmailStr
```

Bad

```python
if "@" not in email:
```

---

# HTTPException Usage

Only routers or global exception handlers may use

```python
HTTPException
```

Services must never import FastAPI.

Repositories must never import FastAPI.

---

# Business Rule Example

Good

```
Booking already completed

↓

BookingAlreadyCompletedError

↓

Router

↓

409 Conflict
```

Bad

```
raise HTTPException(...)
```

inside the service.

---

# Module Independence

Each module owns its own exceptions.

Example

```
auth/exceptions.py

vendors/exceptions.py

bookings/exceptions.py

menu/exceptions.py
```

Modules should not depend on each other's exception files unless intentionally shared through the core exception hierarchy.

---

# Global Exception Registration

Application startup should register

```python
register_exception_handlers(app)
```

exactly once.

No module should register handlers independently.

---

# Testing

Every custom exception should be tested.

Tests should verify

- HTTP status
- response structure
- error code
- message
- logging
- unexpected errors
- validation errors

---

# Future Exception Categories

Planned additions

```
BookingException

PaymentException

AIException

NotificationException

StorageException

MenuException

InventoryException

CampusException
```

---

# AI Development Rules

When generating exception handling code

Always

- inherit from the project hierarchy
- use meaningful exception names
- define stable error codes
- log unexpected errors
- return consistent JSON
- keep services framework-independent

Never

- expose stack traces
- leak SQL errors
- return raw exception strings
- raise HTTPException in repositories
- raise HTTPException in services

---

# Golden Rules

1. Every exception has one responsibility.

2. Services raise business exceptions.

3. Routers translate exceptions into HTTP responses.

4. Global handlers ensure consistent formatting.

5. Never expose internal implementation details.

6. Use stable `error_code` values.

7. Keep exception messages user-friendly.

8. Log enough information for debugging, but never sensitive data.

9. Every module owns its own exception definitions.

10. The exception system must remain centralized, predictable, and easy to extend.

This document is the canonical exception handling guide for the CampusBite AI Backend.