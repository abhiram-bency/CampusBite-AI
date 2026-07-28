# CampusBite AI Backend
## 08_AUTHENTICATION.md

Version: 1.0

Status: Authentication & Authorization Guide

---

# Purpose

This document defines the complete authentication and authorization architecture of the CampusBite AI Backend.

Every authentication-related feature must follow these standards.

The goals are

- secure authentication
- stateless authorization
- modular implementation
- role-based access control
- clean separation of responsibilities

---

# Authentication Stack

The backend uses

```
FastAPI

↓

OAuth2 Password Bearer

↓

JWT Access Tokens

↓

bcrypt Password Hashing

↓

PostgreSQL User Database
```

No session-based authentication is used.

Authentication is completely stateless.

---

# Authentication Flow

```
User

↓

POST /auth/login

↓

Validate credentials

↓

Generate JWT

↓

Return access token

↓

Client stores token

↓

Authorization: Bearer <token>

↓

Protected API

↓

Current User Dependency

↓

Business Logic
```

---

# JWT Standard

The backend uses

```
JSON Web Tokens (JWT)
```

Algorithm

```
HS256
```

JWT Secret

```
settings.SECRET_KEY
```

Configured through environment variables.

Never hardcode secrets.

---

# Password Hashing

Passwords are hashed using

```
bcrypt
```

via

```
passlib
```

Passwords are never stored in plaintext.

---

# Password Flow

Registration

```
Password

↓

bcrypt hash

↓

Database
```

Login

```
Password

↓

Verify against hash

↓

JWT
```

---

# Security Module

All cryptographic operations belong in

```
app/modules/auth/security.py
```

Responsibilities

- hash passwords
- verify passwords
- create JWT
- decode JWT

Nothing else.

---

# Service Layer

Authentication business logic belongs in

```
auth/service.py
```

Responsibilities

- register users
- authenticate users
- uniqueness validation
- account state checks
- issue tokens

---

# Repository Layer

Authentication repositories perform

- user lookup
- email lookup
- registration lookup
- insert user
- insert student
- insert vendor

Repositories never

- hash passwords
- issue JWT
- verify credentials
- raise HTTP exceptions

---

# Router Layer

Routers

- validate requests
- call services
- translate exceptions
- return response models

Routers never contain authentication logic.

---

# JWT Claims

CampusBite access tokens contain

```
sub

role

iat

exp
```

---

## Subject

```
sub
```

Stores

```
User UUID
```

Example

```
"5c09d5d8-..."
```

---

## Role

```
role
```

Stores

```
student

vendor

admin
```

using

```
UserRoleEnum
```

Never store arbitrary strings.

---

## Issued At

```
iat
```

Unix timestamp.

UTC.

---

## Expiration

```
exp
```

Unix timestamp.

UTC.

---

# Token Lifetime

Configured through

```
ACCESS_TOKEN_EXPIRE_MINUTES
```

in Settings.

Never hardcode expiry durations.

---

# Token Creation

Always use

```python
create_access_token()
```

Never build JWT manually.

---

# Token Validation

Always use

```python
decode_access_token()
```

Never call

```python
jose.jwt.decode()
```

outside

```
security.py
```

---

# Current User Resolution

Authentication dependency chain

```
Bearer Token

↓

decode_access_token()

↓

TokenPayload

↓

Repository lookup

↓

User

↓

Route
```

---

# Dependency Hierarchy

The project provides reusable dependencies.

```
get_current_user()

↓

require_student()

↓

require_vendor()

↓

require_admin()
```

All protected routes must use these.

Never duplicate authorization logic.

---

# Role-Based Access Control

Student endpoints

```python
Depends(require_student)
```

Vendor endpoints

```python
Depends(require_vendor)
```

Admin endpoints

```python
Depends(require_admin)
```

Authenticated-only endpoints

```python
Depends(get_current_user)
```

---

# Authorization Flow

```
JWT

↓

Decode

↓

Load User

↓

Verify Active

↓

Verify Role

↓

Endpoint
```

---

# Protected Routes

Examples

```
GET /auth/me

↓

Authenticated User


GET /vendors/me

↓

Vendor


GET /admin/users

↓

Admin


POST /bookings

↓

Student
```

---

# Registration Flow

Student

```
Validate Request

↓

Check Email

↓

Check Registration Number

↓

Hash Password

↓

Create User

↓

Create Student

↓

Return JWT
```

Vendor

```
Validate Request

↓

Check Email

↓

Hash Password

↓

Create User

↓

Create Vendor

↓

Return JWT
```

---

# Login Flow

```
Validate Request

↓

Find User

↓

Verify Password

↓

Check Active

↓

Issue JWT

↓

Return LoginResponse
```

---

# Authentication Responses

Successful login

```
{
    access_token,
    token_type,
    user
}
```

Registration returns exactly the same structure.

---

# Authentication Schemas

Current schemas

```
Token

TokenPayload

LoginRequest

LoginResponse

AuthenticatedUserResponse

StudentRegisterRequest

VendorRegisterRequest
```

---

# Authentication Exceptions

Current module exceptions

```
AuthError

InvalidTokenException

InactiveUserException

InvalidCredentialsException

EmailAlreadyExistsException

RegistrationNumberAlreadyExistsException

InsufficientPermissionsException
```

Services raise these.

Routers convert them into HTTP responses.

---

# HTTP Status Codes

```
200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error
```

---

# HTTPException Rules

Only routers may raise

```python
HTTPException
```

Services never import FastAPI.

Repositories never import FastAPI.

---

# Account State

Every authenticated request must verify

```
user.is_active

AND

user.deleted_at is None
```

Inactive accounts cannot access protected APIs.

---

# Email Handling

Emails are normalized

```
lowercase

trim whitespace
```

using Pydantic validators.

Repositories assume normalized emails.

---

# Password Rules

Minimum

```
8 characters
```

Never

- log passwords
- return passwords
- expose hashes

Passwords use

```
SecretStr
```

---

# Token Storage

Frontend stores

```
Access Token
```

Backend stores nothing.

No server-side sessions.

---

# Logout

Current implementation

```
Client deletes token.
```

Future implementation

```
JWT blacklist

or

Refresh Token rotation
```

---

# Refresh Tokens

Not implemented.

Future roadmap

```
Access Token

↓

Refresh Token

↓

Rotate

↓

Blacklist old token
```

---

# Email Verification

Planned future feature.

```
Register

↓

Email Verification

↓

Activate Account
```

---

# Forgot Password

Planned.

```
Email

↓

Reset Token

↓

Reset Password
```

---

# Multi-Factor Authentication

Future feature.

Possible options

- OTP
- Email verification
- Authenticator apps

---

# Security Logging

Log

- successful login
- failed login
- registration
- invalid token
- permission failures

Never log

- passwords
- JWT secret
- password hashes

---

# Authentication Testing

Authentication tests should cover

- password hashing
- password verification
- JWT creation
- JWT decoding
- expired token
- malformed token
- registration
- login
- role authorization
- protected routes

---

# AI Development Rules

When generating authentication code

Always

- use bcrypt
- use JWT
- use dependency injection
- use service layer
- use repository layer
- use Auth exceptions
- use Pydantic schemas

Never

- hash passwords in routers
- decode JWT outside security.py
- perform SQL in routers
- raise HTTPException from services
- bypass authorization dependencies

---

# Future Authentication Roadmap

Planned features

- Refresh Tokens
- Logout API
- Email Verification
- Password Reset
- Account Lockout
- Login Rate Limiting
- OAuth (Google)
- University SSO
- MFA
- JWT Revocation
- Audit Logs
- Device Management
- Active Session Tracking

---

# Golden Rules

1. Authentication is stateless.

2. JWT is the single authentication mechanism.

3. Passwords are always bcrypt hashed.

4. Security logic belongs only in `security.py`.

5. Business logic belongs only in `service.py`.

6. Routers only translate requests and responses.

7. Role checks must use reusable dependencies.

8. Never trust client-provided roles.

9. Every protected route must resolve the current user.

10. Authentication code must remain modular, testable, and framework-independent wherever possible.

This document is the canonical authentication and authorization guide for the CampusBite AI Backend.