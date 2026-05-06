"""asyncpg connection pool lifecycle management.

The pool is created once at application startup (inside the FastAPI lifespan
context manager) and closed at shutdown. All application code acquires
connections via get_pool() and the get_db() FastAPI dependency.

Pool is configured with:
  - min_size / max_size from settings (default 2 / 10)
  - command_timeout=60s to abort runaway queries
  - application_name for pg_stat_activity visibility
"""

from __future__ import annotations

import logging

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    """
    Open the asyncpg connection pool. Call once at app startup.

    asyncpg.create_pool() accepts individual host/port/user/password/database
    keyword args — NOT a full DSN — so we pass settings fields directly.
    The full settings.asyncpg_url is used only for Alembic (via SQLAlchemy).
    """
    global _pool

    # Parse the asyncpg_url back into components to support both local and
    # Render (DATABASE_URL) configurations without duplicating logic.
    from urllib.parse import urlparse

    parsed = urlparse(settings.asyncpg_url)

    _pool = await asyncpg.create_pool(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        min_size=settings.DB_POOL_MIN_SIZE,
        max_size=settings.DB_POOL_MAX_SIZE,
        command_timeout=60,
        server_settings={"application_name": "ai-summarization-api"},
    )
    logger.info(
        "Database pool created",
        extra={"host": parsed.hostname, "database": parsed.path.lstrip("/")},
    )
    return _pool


async def close_pool() -> None:
    """Close the asyncpg pool. Call once at app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> asyncpg.Pool:
    """
    Return the active connection pool.

    Raises RuntimeError if the pool has not been created yet (i.e., called
    before the FastAPI lifespan startup hook has run).
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialized. "
            "Ensure create_pool() has been called in the app lifespan startup."
        )
    return _pool
