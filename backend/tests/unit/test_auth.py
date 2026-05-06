"""Unit tests for password hashing and JWT encode/decode.

No database or network calls — fully isolated.
All tests run locally even without Docker.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from freezegun import freeze_time
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── Password helpers ───────────────────────────────────────────────────────────

def test_hash_password_is_not_plaintext():
    hashed = hash_password("TestPass123!")
    assert hashed != "TestPass123!"
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_verify_password_correct():
    hashed = hash_password("TestPass123!")
    assert verify_password("TestPass123!", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("TestPass123!")
    assert verify_password("WrongPassword", hashed) is False


def test_different_passwords_produce_different_hashes():
    h1 = hash_password("TestPass123!")
    h2 = hash_password("TestPass123!")
    # bcrypt generates a random salt each time
    assert h1 != h2


# ── Access token ───────────────────────────────────────────────────────────────

def test_access_token_contains_expected_claims():
    token = create_access_token("user-uuid-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-uuid-abc"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_decode_token_returns_dict():
    token = create_access_token("u-123")
    result = decode_token(token)
    assert isinstance(result, dict)


def test_access_token_algorithm_is_hs256():
    token = create_access_token("u-123")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"


# ── Refresh token ──────────────────────────────────────────────────────────────

def test_refresh_token_type_claim():
    token = create_refresh_token("user-uuid-xyz")
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "user-uuid-xyz"


def test_access_and_refresh_tokens_are_different():
    uid = "user-abc"
    access = create_access_token(uid)
    refresh = create_refresh_token(uid)
    assert access != refresh


# ── Token decode security ──────────────────────────────────────────────────────

def test_tampered_token_raises_value_error():
    token = create_access_token("u-123")
    bad_token = token[:-5] + "XXXXX"
    with pytest.raises(ValueError):
        decode_token(bad_token)


def test_wrong_secret_raises_value_error():
    payload = {"sub": "u-123", "type": "access", "exp": 9999999999}
    bad_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
    with pytest.raises(ValueError):
        decode_token(bad_token)


@freeze_time("2026-04-29 12:00:00")
def test_expired_token_raises_value_error():
    """Token whose exp is in the past should raise ValueError."""
    expired_payload = {
        "sub": "u-123",
        "type": "access",
        "exp": datetime(2026, 4, 29, 11, 59, 59, tzinfo=timezone.utc),
    }
    token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(ValueError):
        decode_token(token)


def test_none_algorithm_attack_rejected():
    """
    SEC-07: tokens signed with the 'none' algorithm must be rejected.
    python-jose rejects 'none' when algorithms= is specified explicitly.
    """
    payload = {"sub": "u-123", "type": "access", "exp": 9999999999}
    # Manually craft a none-algorithm token
    import base64, json

    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    none_token = f"{header.decode()}.{body.decode()}."

    with pytest.raises(ValueError):
        decode_token(none_token)
