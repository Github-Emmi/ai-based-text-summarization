"""Chat repository — chat_sessions and chat_messages tables."""

from __future__ import annotations

import uuid
from typing import Optional

from app.db.repositories.base import BaseRepository


class ChatRepository(BaseRepository):

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def create_session(
        self,
        user_id: str,
        title: str,
        summary_id: Optional[str] = None,
    ) -> dict:
        query = """
            INSERT INTO chat_sessions (id, user_id, summary_id, title)
            VALUES (gen_random_uuid(), $1, $2, $3)
            RETURNING id, user_id, summary_id, title, created_at, updated_at
        """
        row = await self._conn.fetchrow(
            query,
            uuid.UUID(user_id),
            uuid.UUID(summary_id) if summary_id else None,
            title,
        )
        return self._serialize_session(dict(row))

    async def get_session(self, session_id: str, user_id: str) -> dict | None:
        query = """
            SELECT id, user_id, summary_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = $1 AND user_id = $2
        """
        row = await self._conn.fetchrow(
            query, uuid.UUID(session_id), uuid.UUID(user_id)
        )
        return self._serialize_session(dict(row)) if row else None

    async def list_sessions(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        offset = (page - 1) * page_size
        user_uuid = uuid.UUID(user_id)

        total: int = await self._conn.fetchval(
            "SELECT COUNT(*) FROM chat_sessions WHERE user_id = $1", user_uuid
        )
        rows = await self._conn.fetch(
            """
            SELECT cs.id, cs.title, cs.summary_id, cs.created_at, cs.updated_at,
                   COUNT(cm.id)::int AS message_count
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cm.session_id = cs.id
            WHERE cs.user_id = $1
            GROUP BY cs.id
            ORDER BY cs.updated_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_uuid,
            page_size,
            offset,
        )
        items = [self._serialize_session(dict(row)) for row in rows]
        return items, total

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        result = await self._conn.execute(
            "DELETE FROM chat_sessions WHERE id = $1 AND user_id = $2",
            uuid.UUID(session_id),
            uuid.UUID(user_id),
        )
        return result == "DELETE 1"

    async def update_session_timestamp(self, session_id: str) -> None:
        await self._conn.execute(
            "UPDATE chat_sessions SET updated_at = NOW() WHERE id = $1",
            uuid.UUID(session_id),
        )

    # ── Messages ──────────────────────────────────────────────────────────────

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None,
    ) -> dict:
        row = await self._conn.fetchrow(
            """
            INSERT INTO chat_messages (id, session_id, role, content, tokens_used)
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
            RETURNING id, role, content, tokens_used, created_at
            """,
            uuid.UUID(session_id),
            role,
            content,
            tokens_used,
        )
        return self._serialize_message(dict(row))

    async def get_messages(
        self, session_id: str, limit: int = 50
    ) -> list[dict]:
        rows = await self._conn.fetch(
            """
            SELECT id, role, content, tokens_used, created_at
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            uuid.UUID(session_id),
            limit,
        )
        return [self._serialize_message(dict(r)) for r in rows]

    async def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> list[dict]:
        return await self.get_messages(session_id, limit=limit)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_session(d: dict) -> dict:
        d["id"] = str(d["id"])
        if d.get("user_id"):
            d["user_id"] = str(d["user_id"])
        if d.get("summary_id"):
            d["summary_id"] = str(d["summary_id"])
        return d

    @staticmethod
    def _serialize_message(d: dict) -> dict:
        d["id"] = str(d["id"])
        return d
