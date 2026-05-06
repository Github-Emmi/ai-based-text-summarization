"""User account endpoints: GET /me and PATCH /me.

Route prefix: /users — included on the app with prefix="/api/v1".
Full paths: GET /api/v1/users/me, PATCH /api/v1/users/me.

All routes require a valid JWT access token (enforced via get_current_user).
"""

from __future__ import annotations

import logging
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ConflictError
from app.core.limiter import limiter
from app.core.security import hash_password
from app.db.repositories.user_repository import UserRepository
from app.schemas.auth import UpdateUserRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def _to_response(user: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=str(user["id"]),
        email=user["email"],
        created_at=user["created_at"],
    )


# ── GET /api/v1/users/me ───────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's profile",
)
@limiter.limit("60/minute")
async def get_me(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return _to_response(current_user)


# ── PATCH /api/v1/users/me ────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the authenticated user's email or password",
)
@limiter.limit("30/minute")
async def update_me(
    request: Request,
    body: UpdateUserRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db),
) -> UserResponse:
    """
    Update email and/or password for the authenticated user.

    - If neither field is provided: returns current profile unchanged (no-op).
    - Email change: 409 if the new email is already taken by another user.
    - Password change: hashed with bcrypt cost=12 before storage.
    - FastAPI caches Depends(get_db) per request, so `conn` here is the same
      connection used inside get_current_user — no double acquire.
    """
    user_id = str(current_user["id"])

    # No-op: nothing to update
    if body.email is None and body.password is None:
        return _to_response(current_user)

    repo = UserRepository(conn)

    # Validate email uniqueness before any write
    if body.email is not None:
        existing = await repo.get_by_email(str(body.email))
        if existing is not None and str(existing["id"]) != user_id:
            raise ConflictError("Email already registered")

    new_hashed = hash_password(body.password) if body.password is not None else None
    updated = await repo.update(
        user_id,
        email=str(body.email) if body.email is not None else None,
        hashed_password=new_hashed,
    )

    logger.info("User profile updated", extra={"user_id": user_id})
    return _to_response(updated)  # type: ignore[arg-type]
