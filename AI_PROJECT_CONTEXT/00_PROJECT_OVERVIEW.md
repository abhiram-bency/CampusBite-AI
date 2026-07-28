# 00_PROJECT_OVERVIEW.md

# CampusBite AI Backend
### Project Overview & Engineering Vision

Version: 1.0
Status: Active Development
Architecture: Modular Monolith
Backend Framework: FastAPI
Language: Python 3.11+
Database: PostgreSQL
ORM: SQLAlchemy 2.x (Async)
Cache: Redis
Authentication: JWT
API Style: REST
Deployment: Docker

---

# 1. Project Overview

CampusBite AI is an AI-powered food pre-booking platform designed specifically for university campuses.

Unlike traditional food delivery applications, CampusBite focuses on helping students pre-order food from campus vendors before arriving at the stall, significantly reducing waiting time during peak hours.

The platform is designed around a WhatsApp-first experience while also supporting dedicated web dashboards for vendors and administrators.

The backend is intentionally designed to be scalable, maintainable, and production-ready from the beginning rather than evolving from a prototype.

---

# 2. Core Vision

CampusBite aims to become the intelligent operating system for campus food services.

The platform should eventually provide:

- AI-powered food recommendations
- Natural language ordering
- WhatsApp chatbot ordering
- Smart stall discovery
- Live menu management
- Queue reduction
- Order scheduling
- Analytics for vendors
- Administrative monitoring
- Multi-campus support

The backend should therefore be written with long-term scalability in mind.

No shortcuts should compromise maintainability.

---

# 3. Primary Users

The system currently supports four major user roles.

## Student

Students can:

- Register
- Login
- Browse stalls
- Browse menus
- Search food
- Place orders
- Schedule pickups
- Track orders
- View order history
- Receive AI recommendations

---

## Vendor

Vendors (stall owners) can:

- Register
- Login
- Manage profile
- Manage stalls
- Manage menus
- View incoming orders
- Accept/reject orders
- Update preparation status
- View analytics

---

## Administrator

Administrators can:

- Manage campuses
- Manage vendors
- Verify vendor accounts
- Monitor platform health
- Moderate content
- Manage users
- Access analytics
- Configure platform settings

---

## AI Services

The AI subsystem provides:

- Food recommendation
- Semantic food search
- Natural language understanding
- WhatsApp chatbot responses
- Recommendation ranking
- Future LLM integrations

The AI module should remain isolated from business modules.

---

# 4. High-Level Architecture

CampusBite follows a layered architecture.

```
                Client Applications

        React Dashboard
        WhatsApp Bot
        Mobile App
        Future Clients

                  │
                  ▼

              FastAPI Routers

                  │
                  ▼

              Service Layer

                  │
                  ▼

            Repository Layer

                  │
                  ▼

          PostgreSQL / Redis
```

Responsibilities are strictly separated.

No layer may bypass another layer.

---

# 5. Architectural Philosophy

The project intentionally follows a Modular Monolith architecture.

Each business domain is isolated into its own module.

Examples:

- auth
- users
- vendors
- students
- stalls
- menu
- orders
- payments
- ai
- notifications

Each module owns:

- router
- service
- repository
- schemas
- exceptions
- tests

Modules communicate only through services.

Repositories must never directly call repositories from another module.

---

# 6. Engineering Goals

This project prioritizes:

- Readability
- Maintainability
- Type safety
- Testability
- Separation of concerns
- Clean architecture
- Production readiness
- Explicitness over magic

Developer convenience is never prioritized over code quality.

---

# 7. Technology Stack

Backend

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x Async
- Alembic
- PostgreSQL
- Redis
- Pydantic v2

Security

- JWT
- Passlib (bcrypt)
- OAuth2 Bearer

Development

- Ruff
- Black
- Pytest
- Docker
- Docker Compose
- GitHub Actions

Future

- Celery
- RabbitMQ (optional)
- OpenTelemetry
- Prometheus
- Grafana

---

# 8. Design Principles

The codebase follows several fundamental engineering principles.

## Single Responsibility Principle

Every class should have one responsibility.

Examples:

Repository

- Database access only

Service

- Business logic only

Router

- HTTP only

Schemas

- Validation only

---

## Dependency Injection

All dependencies are injected.

Services never instantiate repositories.

Routers never instantiate services directly.

Database sessions are injected.

Authentication is dependency-based.

---

## Explicitness

Hidden behavior should be avoided.

Good:

```python
user = await repository.get_user_by_email(email)
```

Avoid:

```python
User.find(email)
```

Explicit code is preferred.

---

## Stateless Services

Services should not maintain mutable state.

Each request is independent.

---

## Composition over Inheritance

Composition is preferred whenever possible.

Inheritance should only be used where it models genuine shared behavior.

---

# 9. API Philosophy

CampusBite exposes a REST API.

Endpoints should:

- be predictable
- use HTTP semantics correctly
- be versioned
- return consistent responses

Example

```
GET     /vendors/me
PATCH   /vendors/me

POST    /auth/login

GET     /stalls

POST    /orders

PATCH   /orders/{id}
```

---

# 10. Security Philosophy

Security is a first-class concern.

Authentication:

JWT

Authorization:

Dependency-based RBAC

Passwords:

bcrypt

Sensitive values:

SecretStr

Input validation:

Pydantic

Database:

Parameterized SQL via SQLAlchemy

No plaintext passwords are ever stored or logged.

---

# 11. Logging Philosophy

Logging exists to help operators understand production behavior.

Logs should answer:

- What happened?
- When?
- Why?
- Which user?
- Which request?

Sensitive information must never be logged.

Examples:

✓ user id

✓ vendor id

✓ request id

✗ passwords

✗ JWTs

✗ secrets

---

# 12. Testing Philosophy

Every feature should eventually include:

- unit tests
- integration tests
- regression tests

Regression tests should accompany every bug fix.

Testing should verify behavior rather than implementation details.

---

# 13. Documentation Philosophy

Every module should be understandable without reading another module.

Every public function should contain a useful docstring.

Complex decisions should explain **why**, not only **what**.

Comments should document intent rather than obvious syntax.

---

# 14. AI-Assisted Development

AI is used as an engineering assistant, not as the architect.

AI-generated code must:

- compile
- pass Ruff
- pass formatting
- follow project architecture
- preserve module boundaries
- avoid duplicate logic
- avoid introducing unnecessary abstractions

Every AI-generated change should be reviewed before acceptance.

---

# 15. Current Project Status

Completed

- Core infrastructure
- Configuration system
- Database layer
- Logging
- Exception framework
- Authentication
- Authorization
- Vendor Profile (Phase 1)

In Progress

- Remaining business modules

Planned

- Stall Management
- Menu Management
- Student Module
- Orders
- Payments
- Notifications
- AI Recommendation Engine
- WhatsApp Integration
- Analytics
- Admin Dashboard

---

# 16. Long-Term Vision

CampusBite is intended to evolve into a production-grade backend capable of serving multiple universities.

Future milestones include:

- Horizontal scalability
- Event-driven processing
- AI personalization
- Recommendation engine
- Voice ordering
- LLM-powered chatbot
- Multi-tenant architecture
- Mobile applications
- Kubernetes deployment
- Observability
- Distributed tracing

The architecture decisions made today should support these future goals without requiring major rewrites.

---

End of Document