"""Password hashing and JWT token utilities.

All functions are pure (no DB calls) and synchronous except where noted.

JWT contract:
- Access token:  type="access",  exp=now + ACCESS_TOKEN_EXPIRE_MINUTES
- Refresh token: type="refresh", exp=now + REFRESH_TOKEN_EXPIRE_DAYS

Security rule (SEC-07 from docs/11-security-checklist.md):
  jwt.decode() MUST specify algorithms=[settings.ALGORITHM] explicitly.
  Omitting the algorithms list allows the "none" algorithm attack.

Note: passlib 1.7.4 is incompatible with bcrypt>=4.1 (removed __about__ module
and strict 72-byte enforcement). We call bcrypt directly instead.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_BCRYPT_ROUNDS = 12


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash ($2b$) of the given plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT helpers ────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    """Create a signed JWT access token valid for ACCESS_TOKEN_EXPIRE_MINUTES."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a signed JWT refresh token valid for REFRESH_TOKEN_EXPIRE_DAYS."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": user_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises ValueError if the token is expired, has an invalid signature,
    or is otherwise malformed. Never raises a library-specific exception —
    callers depend on ValueError to produce a clean 401 response.
    """
    try:
        # algorithms= must be explicit — prevents none-algorithm attack (SEC-07)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
