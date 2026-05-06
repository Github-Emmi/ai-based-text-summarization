"""Base repository with generic CRUD helpers.

All repositories accept an asyncpg Connection (acquired via Depends(get_db))
and return plain Python dicts derived from asyncpg Record objects.

Rule (from docs/04-project-structure.md):
  All database I/O lives here — NEVER in services or route handlers.
  No ORM sessions — raw asyncpg for performance.
  Return dicts, never raw asyncpg Record objects, so callers aren't coupled
  to the asyncpg Row API.
"""

from __future__ import annotations

from typing import Any

import asyncpg


class BaseRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def _fetchrow(self, query: str, *args: Any) -> dict | None:
        """Execute a query and return the first row as a dict, or None."""
        row = await self._conn.fetchrow(query, *args)
        return dict(row) if row else None

    async def _fetch(self, query: str, *args: Any) -> list[dict]:
        """Execute a query and return all rows as a list of dicts."""
        rows = await self._conn.fetch(query, *args)
        return [dict(row) for row in rows]

    async def _execute(self, query: str, *args: Any) -> str:
        """Execute a DML query and return the status string (e.g. 'INSERT 0 1')."""
        return await self._conn.execute(query, *args)

    async def _fetchval(self, query: str, *args: Any) -> Any:
        """Execute a query and return a single scalar value."""
        return await self._conn.fetchval(query, *args)
