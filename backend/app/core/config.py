from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it loads correctly regardless of CWD.
# backend/app/core/config.py → .parent×3 = backend/
_ENV_FILE = str(Path(__file__).resolve().parent.parent.parent / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "AI-Based Text Summarization"
    APP_VERSION: str = "1.0.0"

    # ── Security ───────────────────────────────────────────────────────────────
    # Dev default so the app starts without a .env file during CI/testing.
    # Production MUST override this via env var or Render generateValue.
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database — individual params (local dev / docker-compose) ──────────────
    DB_USER: str = "summarize_user"
    DB_PASSWORD: str = "summarize_pass"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "summarize_db"
    DB_POOL_MIN_SIZE: int = 2
    DB_POOL_MAX_SIZE: int = 10

    # ── Database — full URL (Render injects this; overrides individual params) ─
    DATABASE_URL: Optional[str] = None

    # ── AI — OpenAI / OpenRouter ───────────────────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    # Override to https://openrouter.ai/api/v1 to use OpenRouter
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "meta-llama/llama-3.2-3b-instruct:free"
    OPENAI_MAX_TOKENS: int = 1024
    OPENAI_TEMPERATURE: float = 0.3

    # ── AI — HuggingFace ───────────────────────────────────────────────────────
    HUGGINGFACE_MODEL: str = "facebook/bart-large-cnn"
    USE_LOCAL_MODEL: bool = False
    HUGGINGFACE_API_TOKEN: Optional[str] = None

    # ── File Upload ────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads/"

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # ── Rate Limiting ──────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a Python list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def asyncpg_url(self) -> str:
        """
        DSN for asyncpg.create_pool().
        asyncpg uses the plain 'postgresql://' scheme (not 'postgresql+asyncpg://').
        Render provides DATABASE_URL with 'postgres://' prefix — normalize it.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def alembic_url(self) -> str:
        """
        DSN for SQLAlchemy's async engine used by Alembic migrations.
        SQLAlchemy async requires the 'postgresql+asyncpg://' scheme.
        """
        base = self.asyncpg_url
        if base.startswith("postgresql://"):
            return base.replace("postgresql://", "postgresql+asyncpg://", 1)
        return base


settings = Settings()
