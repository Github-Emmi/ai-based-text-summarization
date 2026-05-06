"""Summary repository — all DB I/O for the summaries table."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from app.db.repositories.base import BaseRepository


def _parse_keywords(value) -> list[str]:
    """asyncpg returns JSONB as a raw JSON string — parse it back to a list."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return list(parsed) if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return list(value)


class SummaryRepository(BaseRepository):

    async def create(
        self,
        *,
        user_id: str,
        input_hash: str,
        original_text: str,
        summary: str,
        format: str,
        summary_length: str,
        word_count: int,
        language: str,
        model_used: str,
        tokens_used: Optional[int],
        keywords: list[str],
        source_type: str,
        original_filename: Optional[str] = None,
    ) -> dict:
        query = """
            INSERT INTO summaries (
                id, user_id, input_hash, original_text, summary,
                format, summary_length, word_count, language,
                model_used, tokens_used, keywords, source_type,
                original_filename
            )
            VALUES (
                gen_random_uuid(), $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10, $11::jsonb, $12,
                $13
            )
            RETURNING id, summary, format, summary_length, word_count, language,
                      model_used, tokens_used, keywords, source_type,
                      original_filename, created_at
        """
        row = await self._conn.fetchrow(
            query,
            user_id,
            input_hash,
            original_text,
            summary,
            format,
            summary_length,
            word_count,
            language,
            model_used,
            tokens_used,
            json.dumps(keywords),
            source_type,
            original_filename,
        )
        result = dict(row)
        # Normalize JSONB → Python list (asyncpg returns JSONB as JSON string)
        result["keywords"] = _parse_keywords(result.get("keywords"))
        result["id"] = str(result["id"])
        return result

    async def get_by_id(self, summary_id: str, user_id: str) -> dict | None:
        query = """
            SELECT id, summary, format, summary_length, word_count, language,
                   model_used, tokens_used, keywords, source_type,
                   original_filename, original_text, created_at
            FROM summaries
            WHERE id = $1 AND user_id = $2
        """
        row = await self._conn.fetchrow(query, uuid.UUID(summary_id), uuid.UUID(user_id))
        if not row:
            return None
        result = dict(row)
        result["keywords"] = _parse_keywords(result.get("keywords"))
        result["id"] = str(result["id"])
        return result

    async def list_by_user(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 10,
        source_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        """Return (items, total_count)."""
        offset = (page - 1) * page_size
        base_cond = "WHERE user_id = $1"
        params: list[Any] = [uuid.UUID(user_id)]

        if source_type:
            base_cond += f" AND source_type = ${len(params) + 1}"
            params.append(source_type)

        if keyword:
            # JSONB GIN index: keywords array contains the given string
            base_cond += f" AND keywords @> ${len(params) + 1}::jsonb"
            params.append(json.dumps([keyword.lower()]))

        count_query = f"SELECT COUNT(*) FROM summaries {base_cond}"
        total: int = await self._conn.fetchval(count_query, *params)

        n = len(params)
        list_query = f"""
            SELECT id, summary, format, summary_length, word_count, language,
                   model_used, tokens_used, keywords, source_type,
                   original_filename, created_at
            FROM summaries
            {base_cond}
            ORDER BY created_at DESC
            LIMIT ${n + 1} OFFSET ${n + 2}
        """
        rows = await self._conn.fetch(list_query, *params, page_size, offset)
        items = []
        for row in rows:
            d = dict(row)
            d["keywords"] = _parse_keywords(d.get("keywords"))
            d["id"] = str(d["id"])
            items.append(d)
        return items, total

    async def delete(self, summary_id: str, user_id: str) -> bool:
        query = """
            DELETE FROM summaries WHERE id = $1 AND user_id = $2
        """
        result = await self._conn.execute(
            query, uuid.UUID(summary_id), uuid.UUID(user_id)
        )
        return result == "DELETE 1"
