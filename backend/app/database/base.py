"""Base SQLAlchemy declarative model.

Moved from `app/core/base_model.py` as part of the `app/database/`
infrastructure refactor. Every ORM model in every business module MUST
inherit from `Base` (directly or via `BaseModel`) so that Alembic
autogeneration and the shared metadata registry work consistently
across the whole project.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

from app.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Base(DeclarativeBase):
    """Project-wide declarative base.

    All ORM models must inherit from this class so Alembic's
    ``target_metadata`` can discover every table via a single metadata
    object.
    """

    pass


class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Convenience base combining UUID PK + audit timestamps.

    Most domain entities should inherit from this class rather than
    composing the mixins manually. Add `SoftDeleteMixin` (from
    `app.database.mixins`) explicitly on models that need soft delete.
    """

    __abstract__ = True
