"""Integration tests for chat endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

MOCK_CHAT_RESULT = {
    "text": "AI is used in many applications including NLP and computer vision.",
    "model": "gpt-4o-mini",
    "tokens_used": 40,
}


# ── POST /api/v1/chat ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_creates_new_session(auth_client, auth_headers):
    with patch(
        "app.services.chat_service.route_chat",
        new_callable=AsyncMock,
        return_value=MOCK_CHAT_RESULT,
    ):
        resp = await auth_client.post(
            "/api/v1/chat",
            json={"message": "Tell me about AI", "session_id": None},
            headers=auth_headers,
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["session_id"]
    assert data["reply"] == MOCK_CHAT_RESULT["text"]
    assert data["message_id"]


@pytest.mark.asyncio
async def test_chat_continues_existing_session(auth_client, auth_headers):
    with patch(
        "app.services.chat_service.route_chat",
        new_callable=AsyncMock,
        return_value=MOCK_CHAT_RESULT,
    ):
        r1 = await auth_client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
            headers=auth_headers,
        )
        session_id = r1.json()["session_id"]

        r2 = await auth_client.post(
            "/api/v1/chat",
            json={"message": "Follow-up question", "session_id": session_id},
            headers=auth_headers,
        )
    assert r2.status_code == 200
    assert r2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_chat_invalid_session(auth_client, auth_headers):
    with patch(
        "app.services.chat_service.route_chat",
        new_callable=AsyncMock,
        return_value=MOCK_CHAT_RESULT,
    ):
        resp = await auth_client.post(
            "/api/v1/chat",
            json={"message": "Hello", "session_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
    assert resp.status_code == 404


# ── GET /api/v1/chat/{session_id} ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_session_history(auth_client, auth_headers):
    with patch(
        "app.services.chat_service.route_chat",
        new_callable=AsyncMock,
        return_value=MOCK_CHAT_RESULT,
    ):
        r = await auth_client.post(
            "/api/v1/chat",
            json={"message": "What is NLP?"},
            headers=auth_headers,
        )
        session_id = r.json()["session_id"]

    resp = await auth_client.get(f"/api/v1/chat/{session_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert len(data["messages"]) == 2  # user + assistant


@pytest.mark.asyncio
async def test_get_session_not_found(auth_client, auth_headers):
    resp = await auth_client.get(
        f"/api/v1/chat/{uuid.uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


# ── DELETE /api/v1/chat/{session_id} ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_session(auth_client, auth_headers):
    with patch(
        "app.services.chat_service.route_chat",
        new_callable=AsyncMock,
        return_value=MOCK_CHAT_RESULT,
    ):
        r = await auth_client.post(
            "/api/v1/chat",
            json={"message": "Test message"},
            headers=auth_headers,
        )
        session_id = r.json()["session_id"]

    resp = await auth_client.delete(f"/api/v1/chat/{session_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp2 = await auth_client.get(f"/api/v1/chat/{session_id}", headers=auth_headers)
    assert resp2.status_code == 404
