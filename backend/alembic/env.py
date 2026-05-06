"""Alembic migration environment configuration.

Uses SQLAlchemy's async engine (postgresql+asyncpg://) so that we never need
psycopg2. The DSN comes exclusively from app.core.config.settings.alembic_url,
which handles both local dev (individual DB params) and Render (DATABASE_URL).

All four models are imported here so that autogenerate can detect schema changes.
Import order matters for foreign key resolution: users → summaries → chat_sessions
→ chat_messages.
"""

import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ── Make sure 'backend/' is on the Python path when running alembic from there ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402

# Import ALL models so Alembic autogenerate picks up every table.
from app.db.models.base import Base  # noqa: E402
from app.db.models import user, summary, chat_session, chat_message  # noqa: F401, E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares this metadata against the live DB schema.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection ('offline' mode).
    Useful for generating a SQL script: alembic upgrade head --sql
    """
    context.configure(
        url=settings.alembic_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async SQLAlchemy engine and run migrations through it."""
    engine = create_async_engine(
        settings.alembic_url,
        poolclass=pool.NullPool,  # NullPool: never reuse connections in migration runs
    )
    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
