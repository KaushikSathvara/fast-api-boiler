"""Application configuration via Pydantic BaseSettings.

Environment variables are loaded from `.env` (if present) and system env.
Use `get_settings()` for dependency injection via `Annotated[Settings, Depends(get_settings)]`.
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__: list[str] = ["Settings", "get_settings"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────
    PROJECT_NAME: str = "MyProject"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: str = "*"

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: PostgresDsn  # postgresql+asyncpg://user:pass@host/db
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY: str = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" | "console"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Ensure LOG_FORMAT is either 'json' or 'console'."""
        if v not in ("json", "console"):
            msg = "LOG_FORMAT must be 'json' or 'console'"
            raise ValueError(msg)
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (singleton)."""
    return Settings()  # type: ignore[call-arg]
