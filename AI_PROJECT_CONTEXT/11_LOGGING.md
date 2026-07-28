# CampusBite AI Backend
## 11_LOGGING.md

Version: 1.0

Status: Canonical Logging Standards

---

# Purpose

This document defines the complete logging architecture for the CampusBite AI Backend.

Every module must follow these logging standards so that logs remain

- consistent
- searchable
- structured
- production-ready
- secure
- useful for debugging and monitoring

Logging should help developers understand what happened without exposing sensitive information.

---

# Logging Philosophy

Logging is for developers and operators, **not API clients**.

Clients receive clean error responses.

Developers receive structured logs.

```
Request

↓

Router

↓

Service

↓

Repository

↓

Database

↓

Logs
```

---

# Objectives

The logging system should

- simplify debugging
- support production monitoring
- enable centralized log aggregation
- help investigate incidents
- support audit trails
- avoid exposing secrets

---

# Logging Architecture

```
FastAPI

↓

Application Logger

↓

Structured Log Records

↓

Console (Development)

↓

JSON Logs (Production)

↓

ELK / Grafana / Cloud Logging (Future)
```

---

# Logger Creation

Always create module-specific loggers.

Example

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

Never use

```python
print(...)
```

or

```python
logging.getLogger(...)
```

directly.

---

# Logger Location

Every module owns its own logger.

Example

```
auth/security.py

auth/service.py

vendors/service.py

bookings/service.py
```

Each file creates

```python
logger = get_logger(__name__)
```

once.

---

# Logging Levels

CampusBite uses five standard levels.

```
DEBUG

INFO

WARNING

ERROR

CRITICAL
```

---

# DEBUG

Used only during development.

Examples

- decoded JWT payload
- SQL query timing
- cache hit/miss
- request lifecycle
- repository execution details

Example

```python
logger.debug(
    "Decoded JWT payload",
    extra={"extra_fields": {"user_id": str(user.id)}},
)
```

---

# INFO

Represents successful business events.

Examples

- user login
- vendor registration
- booking created
- profile updated
- payment completed

Example

```python
logger.info(
    "Vendor profile updated",
    extra={
        "extra_fields": {
            "user_id": str(user.id),
            "fields": list(updated_fields),
        }
    },
)
```

---

# WARNING

Represents expected failures or suspicious situations.

Examples

- invalid credentials
- inactive account
- permission denied
- malformed JWT
- missing vendor profile

Example

```python
logger.warning(
    "Invalid login attempt",
    extra={
        "extra_fields": {
            "email": payload.email,
        }
    },
)
```

---

# ERROR

Represents unexpected failures.

Examples

- database unavailable
- Redis unavailable
- third-party API failure
- payment gateway failure

Example

```python
logger.error(
    "Database connection failed",
    exc_info=True,
)
```

---

# CRITICAL

Used only for failures that threaten application availability.

Examples

- application startup failure
- configuration corruption
- secret missing
- database unavailable during startup
- catastrophic infrastructure failure

---

# Structured Logging

CampusBite uses structured logging.

Never build long formatted strings.

Bad

```python
logger.info(f"Vendor {vendor.id} updated profile.")
```

Good

```python
logger.info(
    "Vendor profile updated",
    extra={
        "extra_fields": {
            "vendor_id": str(vendor.user_id),
        }
    },
)
```

---

# Standard Log Fields

Whenever possible include

```
user_id

vendor_id

booking_id

stall_id

campus_id

request_id

order_id
```

Only include fields relevant to the event.

---

# Request Logging

Every request should eventually produce logs for

```
method

path

status_code

response_time
```

Future middleware may add

```
request_id

client_ip

user_agent
```

---

# Authentication Logging

Log

- successful login
- failed login
- invalid token
- expired token
- inactive account
- logout

Never log

- password
- password hash
- JWT token
- refresh token
- secret key

Example

```python
logger.warning(
    "Invalid login attempt",
    extra={
        "extra_fields": {
            "email": payload.email,
        }
    },
)
```

---

# Authorization Logging

Log

```
permission denied

role mismatch

admin access

suspicious access attempts
```

Example

```python
logger.warning(
    "Unauthorized admin endpoint access",
    extra={
        "extra_fields": {
            "user_id": str(user.id),
            "role": user.role.value,
        }
    },
)
```

---

# Repository Logging

Repositories generally should **not** log normal database operations.

Repositories only log

- unexpected SQL failures
- integrity failures (when appropriate)
- connection failures

Business events belong in the service layer.

---

# Service Logging

Services own business-event logging.

Examples

```
booking created

vendor verified

profile updated

payment initiated

AI recommendation generated
```

---

# Router Logging

Routers should rarely log.

Routers only

- translate exceptions
- call services
- return responses

Business logging belongs in services.

---

# Startup Logging

Application startup should log

```
environment

project name

database status

Redis status

startup completion
```

Example

```python
logger.info(
    "Starting %s [%s]",
    settings.PROJECT_NAME,
    settings.ENVIRONMENT.value,
)
```

---

# Shutdown Logging

Shutdown should log

```
application shutdown

database disposal

Redis shutdown
```

---

# Sensitive Data Policy

Never log

- passwords
- password hashes
- JWTs
- secret keys
- payment details
- card numbers
- OTPs
- API secrets
- refresh tokens

---

# Personally Identifiable Information

Avoid logging

- phone numbers
- email addresses
- addresses

Instead prefer

```
user_id

vendor_id

booking_id
```

If an email is necessary for debugging, log it only at `WARNING` or lower and avoid including other sensitive identifiers in the same entry.

---

# Exception Logging

Expected business exceptions

```
InvalidCredentialsException

VendorProfileNotFoundError

EmailAlreadyExistsException
```

should usually log as

```
WARNING
```

Unexpected exceptions

should log as

```
ERROR
```

with

```python
exc_info=True
```

---

# Performance Logging

Future middleware may log

```
execution time

database query count

cache hit ratio

AI inference latency
```

---

# JSON Logging

Production deployments should emit JSON logs.

Example

```json
{
    "timestamp": "...",
    "level": "INFO",
    "logger": "app.modules.vendors.service",
    "message": "Vendor profile updated",
    "user_id": "...",
    "fields": [
        "business_name"
    ]
}
```

---

# Development Logging

Development may use human-readable formatting.

Example

```
INFO app.modules.auth.service

Vendor profile updated

user_id=...

fields=['business_name']
```

---

# Correlation IDs

Future middleware should attach

```
request_id
```

to every log entry.

Example

```
request_id

↓

Router

↓

Service

↓

Repository
```

This enables tracing a single request across the application.

---

# AI Module Logging

When AI modules are implemented, log

- prompt version
- model name
- latency
- token usage
- cache usage

Never log

- private user prompts containing sensitive information
- API keys
- provider secrets

---

# Redis Logging

Log

- connection failures
- cache failures
- reconnect attempts

Do not log every cache hit.

---

# Database Logging

Do not log every SQL statement in production.

Enable SQL echo only during development or debugging.

---

# External API Logging

Log

- endpoint
- response time
- status code

Do not log

- authorization headers
- bearer tokens
- secrets

---

# Testing

Logging tests should verify

- expected events are logged
- correct log level
- sensitive information is absent
- structured fields exist

---

# Future Logging Integrations

Planned support

- ELK Stack
- Grafana Loki
- OpenTelemetry
- Prometheus
- CloudWatch
- Azure Monitor
- Google Cloud Logging
- Sentry

---

# AI Development Rules

When generating logging code

Always

- use `get_logger(__name__)`
- use structured logging
- log meaningful events
- use appropriate log levels
- include contextual identifiers
- avoid duplicate logs

Never

- use `print()`
- log passwords
- log JWTs
- log secrets
- log raw SQL queries in production
- log entire request bodies containing sensitive information

---

# Golden Rules

1. Every module owns its own logger.

2. Services log business events.

3. Repositories log infrastructure failures only.

4. Routers should rarely log.

5. Never log secrets.

6. Use structured logging with `extra_fields`.

7. Use the correct log level.

8. Log enough context to debug issues.

9. Production logs should be machine-readable.

10. Logging should aid observability without compromising security.

This document is the canonical logging guide for the CampusBite AI Backend.