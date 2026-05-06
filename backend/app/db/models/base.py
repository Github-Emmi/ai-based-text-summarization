"""SQLAlchemy declarative base and shared column helpers.

All models inherit from Base. TimestampMixin provides created_at / updated_at
columns with server-side defaults so they work correctly even when rows are
inserted via raw asyncpg queries (Alembic generates the DDL from these models).
"""

import uuid

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Add created_at and updated_at columns to any model that inherits this mixin."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def uuid_pk() -> Column:
    """Shorthand for a UUID primary key column with server-side generation."""
    return Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
