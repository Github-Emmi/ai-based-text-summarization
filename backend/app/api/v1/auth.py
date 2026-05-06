"""Auth endpoints: register, login, refresh.

Route prefix: /auth  (NO /api/v1/ — these are public, pre-auth endpoints)

Rate limits (SEC-08):
  - POST /auth/register : 10/minute
  - POST /auth/login    : 5/minute  ← strict; brute-force prevention
  - POST /auth/refresh  : 10/minute

Every rate-limited route must include `request: Request` as a plain parameter
(not Depends) — slowapi reads it directly.
"""

from __future__ import annotations

import logging

import asyncpg
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.core.dependencies import get_db
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_EXPIRES_SECONDS = 30 * 60  # 30 minutes in seconds


# ── POST /auth/register ────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    conn: asyncpg.Connection = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account.

    - Validates email uniqueness (409 if taken).
    - Hashes password with bcrypt cost=12 (SEC-02).
    - Returns the created user (no token — user must login separately).
    """
    repo = UserRepository(conn)

    existing = await repo.get_by_email(str(body.email))
    if existing is not None:
        raise ConflictError("Email already registered")

    hashed = hash_password(body.password)
    user = await repo.create(str(body.email), hashed)

    logger.info("User registered", extra={"user_id": str(user["id"])})
    return UserResponse(
        id=str(user["id"]),
        email=user["email"],
        created_at=user["created_at"],
    )


# ── POST /auth/login ───────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive JWT tokens",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    conn: asyncpg.Connection = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.

    Returns an access token (30 min) and a refresh token (7 days).
    Returns 401 for both "email not found" and "wrong password" — no
    distinction is made to avoid user enumeration (SEC-10).
    """
    repo = UserRepository(conn)

    user = await repo.get_by_email(str(body.email))
    if user is None or not verify_password(body.password, user["hashed_password"]):
        raise UnauthorizedError("Invalid email or password")

    if not user["is_active"]:
        raise UnauthorizedError("Account is inactive")

    user_id = str(user["id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    logger.info("User logged in", extra={"user_id": user_id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_ACCESS_EXPIRES_SECONDS,
    )


# ── POST /auth/refresh ─────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate access and refresh tokens",
)
@limiter.limit("10/minute")
async def refresh_tokens(
    request: Request,
    body: RefreshRequest,
    conn: asyncpg.Connection = Depends(get_db),
) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access token + refresh token pair.

    Validates that the token type claim is "refresh" (SEC-07).
    Returns 401 if the token is invalid, expired, or wrong type.
    """
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise UnauthorizedError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    # Verify the user still exists and is active
    repo = UserRepository(conn)
    user = await repo.get_by_id(user_id)
    if user is None or not user["is_active"]:
        raise UnauthorizedError("User not found or inactive")

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)

    logger.info("Tokens refreshed", extra={"user_id": user_id})
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=_ACCESS_EXPIRES_SECONDS,
    )
