from __future__ import annotations

from typing import Any

import asyncpg

from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self._fetchrow(
            "SELECT id, email, hashed_password, is_active, created_at, updated_at "
            "FROM users WHERE id = $1",
            user_id,
        )

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._fetchrow(
            "SELECT id, email, hashed_password, is_active, created_at, updated_at "
            "FROM users WHERE email = $1",
            email,
        )

    async def create(self, email: str, hashed_password: str) -> dict[str, Any]:
        return await self._fetchrow(
            "INSERT INTO users (email, hashed_password) "
            "VALUES ($1, $2) "
            "RETURNING id, email, is_active, created_at",
            email,
            hashed_password,
        )

    async def update(
        self,
        user_id: str,
        email: str | None = None,
        hashed_password: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update mutable user fields. Only non-None arguments are written.

        Column names in the SET clause are hardcoded (not user-controlled),
        so building the clause with string concatenation is safe — values
        remain fully parameterized ($1, $2, ...) against SQL injection.
        """
        if email is None and hashed_password is None:
            return await self.get_by_id(user_id)

        sets: list[str] = []
        params: list[Any] = []
        idx = 1

        if email is not None:
            sets.append(f"email = ${idx}")
            params.append(email)
            idx += 1
        if hashed_password is not None:
            sets.append(f"hashed_password = ${idx}")
            params.append(hashed_password)
            idx += 1

        sets.append("updated_at = NOW()")
        params.append(user_id)

        sql = (
            f"UPDATE users SET {', '.join(sets)} "
            f"WHERE id = ${idx} "
            "RETURNING id, email, is_active, created_at, updated_at"
        )
        return await self._fetchrow(sql, *params)
