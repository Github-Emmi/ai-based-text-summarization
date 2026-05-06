"""Integration tests for auth and user endpoints.

These tests require a running PostgreSQL database.
They are automatically skipped when no DB is available (see conftest.db_pool).

All tests use the `auth_client` fixture which:
  - Overrides get_db with a per-test transactional connection
  - Rolls back after each test for a clean state
"""

from __future__ import annotations

import pytest


# ── POST /auth/register ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_creates_user(auth_client):
    resp = await auth_client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "StrongPass1!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(auth_client, test_user):
    resp = await auth_client.post("/auth/register", json={
        "email": "test@example.com",   # already inserted by test_user fixture
        "password": "AnotherPass1!",
    })
    assert resp.status_code == 409
    assert resp.json()["error"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_weak_password_returns_422(auth_client):
    resp = await auth_client.post("/auth/register", json={
        "email": "weak@example.com",
        "password": "nodigits",     # no digit or special char
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(auth_client):
    resp = await auth_client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "StrongPass1!",
    })
    assert resp.status_code == 422


# ── POST /auth/login ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_returns_tokens(auth_client, test_user):
    resp = await auth_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(auth_client, test_user):
    resp = await auth_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPass1!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(auth_client):
    resp = await auth_client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "Test1234!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_same_response_as_wrong_password(auth_client, test_user):
    """
    SEC-10: both bad-email and bad-password return 401 with identical error code.
    No user enumeration possible.
    """
    resp_bad_email = await auth_client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "Test1234!",
    })
    resp_bad_pass = await auth_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPass1!",
    })
    assert resp_bad_email.status_code == resp_bad_pass.status_code == 401
    assert resp_bad_email.json()["error"] == resp_bad_pass.json()["error"]


# ── POST /auth/refresh ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(auth_client, test_user):
    # Login first to get a refresh token
    login_resp = await auth_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!",
    })
    assert login_resp.status_code == 200
    old_refresh = login_resp.json()["refresh_token"]

    # Refresh
    resp = await auth_client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_returns_401(auth_client, test_user):
    """SEC-07: passing an access token to /refresh must be rejected."""
    login_resp = await auth_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!",
    })
    access_token = login_resp.json()["access_token"]

    resp = await auth_client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_returns_401(auth_client):
    resp = await auth_client.post("/auth/refresh", json={"refresh_token": "not.a.token"})
    assert resp.status_code == 401


# ── GET /api/v1/users/me ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_returns_user(auth_client, test_user, auth_headers):
    resp = await auth_client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["id"] == str(test_user["id"])
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_without_token_returns_401(auth_client):
    resp = await auth_client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_refresh_token_returns_401(auth_client, test_user):
    """SEC-07: refresh tokens must not be accepted on protected API routes."""
    from app.core.security import create_refresh_token
    bad_token = create_refresh_token(str(test_user["id"]))
    resp = await auth_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401


# ── PATCH /api/v1/users/me ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_me_update_password(auth_client, test_user, auth_headers):
    resp = await auth_client.patch(
        "/api/v1/users/me",
        json={"password": "NewPass123!"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_patch_me_update_email(auth_client, test_user, auth_headers):
    resp = await auth_client.patch(
        "/api/v1/users/me",
        json={"email": "updated@example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_patch_me_noop_returns_current_user(auth_client, test_user, auth_headers):
    resp = await auth_client.patch(
        "/api/v1/users/me",
        json={},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_patch_me_email_conflict_returns_409(auth_client, test_user, auth_headers):
    # Create a second user
    await auth_client.post("/auth/register", json={
        "email": "second@example.com",
        "password": "AnotherPass1!",
    })
    # Try to take second user's email
    resp = await auth_client.patch(
        "/api/v1/users/me",
        json={"email": "second@example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
