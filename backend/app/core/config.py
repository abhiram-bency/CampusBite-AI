"""Application configuration.

Centralized, type-safe configuration loaded from environment variables
(and an optional ``.env`` file) using Pydantic v2 settings management.

All other parts of the application MUST read configuration through the
:func:`get_settings` accessor rather than reading ``os.environ`` directly.
This keeps configuration testable, cacheable, and centrally documented.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Supported deployment environments."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are sourced, in order of precedence, from: process environment
    variables, then a ``.env`` file in the working directory, then the
    defaults declared below.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "CampusBite AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Environment = Environment.LOCAL
    DEBUG: bool = False

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Used for signing tokens. Must be overridden in every "
        "non-local environment.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: str = Field(
        default="",
        description="Comma-separated list of allowed CORS origins, "
        "e.g. 'http://localhost:5173,https://admin.campusbite.app'.",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return :attr:`BACKEND_CORS_ORIGINS` parsed into a list of origins."""
        if not self.BACKEND_CORS_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]


    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------
    POSTGRES_SCHEME: str = "postgresql+asyncpg"
    POSTGRES_USER: str = "campusbite"
    POSTGRES_PASSWORD: str = "campusbite"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "campusbite"
    DATABASE_URL: PostgresDsn | None = None

    # SQLAlchemy engine tuning
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO_SQL: bool = False

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: RedisDsn | None = None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ------------------------------------------------------------------
    # External services (placeholders for future milestones)
    # ------------------------------------------------------------------
    WHATSAPP_CLOUD_API_TOKEN: str | None = None
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, value: str | None, info) -> str:
        """Build the async PostgreSQL DSN if not explicitly provided."""
        if isinstance(value, str) and value:
            return value

        data = info.data
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        host = data.get("POSTGRES_HOST")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB")
        scheme = data.get("POSTGRES_SCHEME", "postgresql+asyncpg")
        return f"{scheme}://{user}:{password}@{host}:{port}/{db}"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, value: str | None, info) -> str:
        """Build the Redis DSN if not explicitly provided."""
        if isinstance(value, str) and value:
            return value

        data = info.data
        host = data.get("REDIS_HOST")
        port = data.get("REDIS_PORT")
        db = data.get("REDIS_DB")
        password = data.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{host}:{port}/{db}"

    @property
    def is_production(self) -> bool:
        """Return ``True`` when running in the production environment."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_local(self) -> bool:
        """Return ``True`` when running in the local dev environment."""
        return self.ENVIRONMENT == Environment.LOCAL


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide :class:`Settings` instance.

    ``lru_cache`` ensures the environment is parsed only once per process
    while still allowing tests to override settings via dependency
    overrides or by clearing the cache with ``get_settings.cache_clear()``.
    """
    return Settings()
