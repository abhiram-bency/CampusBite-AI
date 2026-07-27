"""Database infrastructure package.

Contains the SQLAlchemy declarative base and mixins (`base.py`,
`mixins.py`), the async engine (`engine.py`), and session management
(`session.py`). Replaces the former `app/core/database.py` and
`app/core/base_model.py` (moved here in the infrastructure refactor).

Business modules should import from here (or from
`app.core.dependencies`, which wraps `get_session` as a FastAPI
dependency) rather than reaching into individual submodules directly,
where practical.
"""

from app.database.base import Base, BaseModel
from app.database.engine import check_database_connection, dispose_engine, engine
from app.database.session import AsyncSessionLocal, get_session, session_scope

__all__ = [
    "Base",
    "BaseModel",
    "engine",
    "check_database_connection",
    "dispose_engine",
    "AsyncSessionLocal",
    "get_session",
    "session_scope",
]
