# CampusBite AI

AI-powered, WhatsApp-first food pre-booking platform for university campuses.

Students interact primarily through WhatsApp. The React dashboard serves
**Stall Owners** and **University Administrators** only.

## Architecture (frozen)

```
Conversation Layer → Intent Engine → Domain Services → Repositories → PostgreSQL
```

The AI layer never queries PostgreSQL directly — it only calls backend
domain-service tools.

## Backend structure (frozen)

```
backend/
  app/
    core/          # config, logging, db, redis, base model, DI, exceptions
    conversation/   # WhatsApp inbound/outbound message handling
    modules/        # business domains (students, stalls, bookings, ...)
    ai/             # intent engine, tool calling, RAG, recommendations
  tests/
  scripts/
  alembic/
  main.py
```

Each business module (added in future milestones) follows:

```
modules/<name>/
  api/
  service/
  repository/
  models/
  schemas/
  dependencies/
  utils/
```

## Milestone 1 — Project Bootstrap & Core Infrastructure

This milestone establishes the foundation only. No business logic,
authentication, or business APIs are implemented yet.

Delivered:
- Frozen folder structure
- FastAPI application factory with lifespan startup/shutdown
- Pydantic Settings-based configuration (`app/core/config.py`)
- Centralized logging (`app/core/logging.py`)
- Async SQLAlchemy 2.x engine/session setup (`app/core/database.py`)
- Alembic configuration wired to the async engine
- Redis async connection management (`app/core/redis.py`)
- Base declarative ORM model + mixins (`app/core/base_model.py`)
- Dependency-injection helpers (`app/core/dependencies.py`)
- Centralized exception hierarchy + handlers (`app/core/exceptions.py`)
- Dockerfile (multi-stage) + docker-compose.yml (backend, PostgreSQL, Redis)
- `.env.example`, `requirements.txt`, `pyproject.toml`
- Pre-commit hooks (ruff, mypy, hygiene checks)
- GitHub Actions CI (lint, type-check, test)

## Getting started (local development)

```bash
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

### Run with Docker Compose (recommended)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`, with:
- Health check: `GET /api/v1/health`
- Swagger docs: `GET /api/v1/docs`

### Run tests

```bash
cd backend
pytest -v
```

### Verify infrastructure connectivity

```bash
cd backend
python -m scripts.check_infra
```

### Database migrations (Alembic)

No models exist yet in Milestone 1, so no migrations have been
generated. Once business modules are added:

```bash
cd backend
alembic revision --autogenerate -m "add <module> tables"
alembic upgrade head
```

## Roadmap

Future milestones (not implemented yet): student authentication via
registration number, stall/menu management, bookings, payments,
WhatsApp conversation layer, AI intent engine and tool calling,
semantic search, recommendations, queue optimization, ETA prediction,
RAG-based FAQ, and the React admin/vendor dashboard.
