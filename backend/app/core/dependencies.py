"""FastAPI dependency callables shared across route handlers.

- get_db():           yields an asyncpg Connection from the pool.
- get_current_user(): validates the JWT Bearer token (Phase 3 full impl;
                      Phase 1 raises NotImplementedError if called).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.session import get_pool

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Yield a single asyncpg connection from the global pool.

    Usage in a route:
        async def my_route(conn: asyncpg.Connection = Depends(get_db)):
            row = await conn.fetchrow("SELECT ...", ...)

    The connection is automatically returned to the pool when the route
    handler finishes (even on exception).
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: asyncpg.Connection = Depends(get_db),
) -> dict[str, Any]:
    """
    Validate a JWT Bearer token and return the authenticated user record.

    Full implementation added in Phase 3. Raises 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.core.security import decode_token
    from app.db.repositories.user_repository import UserRepository

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    repo = UserRepository(conn)
    user = await repo.get_by_id(user_id)

    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
