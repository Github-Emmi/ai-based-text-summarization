"""Pydantic schemas for authentication and user management.

Conventions:
- Request schemas validate + coerce inbound data.
- Response schemas shape outbound JSON (no hashed_password ever exposed).
- EmailStr requires email-validator (installed via pydantic[email]).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"
)


class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Enforce: min 8 chars, ≥1 uppercase, ≥1 digit, ≥1 special char (@$!%*?&).
        Docs reference: docs/06-api-design.md — POST /auth/register Validation.
        """
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "at least one uppercase letter, one digit, and one special character (@$!%*?&)."
            )
        return v


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh."""

    refresh_token: str


class UpdateUserRequest(BaseModel):
    """Body for PATCH /api/v1/users/me. All fields optional."""

    email: Optional[EmailStr] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "at least one uppercase letter, one digit, and one special character (@$!%*?&)."
            )
        return v


# ── Responses ─────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Returned by POST /auth/login and POST /auth/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds; 1800 = 30 minutes


class UserResponse(BaseModel):
    """Returned by POST /auth/register, GET /api/v1/users/me, PATCH /api/v1/users/me."""

    id: str
    email: str
    created_at: datetime
