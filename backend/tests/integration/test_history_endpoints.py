"""Integration tests for history endpoints (summary list, get, delete)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest


LONG_TEXT = (
    "Natural language processing (NLP) is an interdisciplinary subfield of "
    "linguistics, computer science, and artificial intelligence concerned with "
    "the interactions between computers and human language, in particular how to "
    "program computers to process and analyze large amounts of natural language data. "
    "The goal is a computer capable of understanding the contents of documents, "
    "including the contextual nuances of the language within them. "
) * 4

MOCK_AI_RESULT = {
    "text": "NLP enables computers to process human language.",
    "model": "gpt-4o-mini",
    "tokens_used": 30,
}


async def _create_summary(auth_client, auth_headers) -> dict:
    with patch(
        "app.services.summarizer.route_summarize",
        new_callable=AsyncMock,
        return_value=MOCK_AI_RESULT,
    ):
        resp = await auth_client.post(
            "/api/v1/summarize/text",
            json={"text": LONG_TEXT, "summary_length": "medium"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    return resp.json()


# ── GET /api/v1/history/summaries ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_summaries_empty(auth_client, auth_headers):
    resp = await auth_client.get("/api/v1/history/summaries", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["pagination"]["total_items"] == 0


@pytest.mark.asyncio
async def test_list_summaries_returns_item(auth_client, auth_headers):
    summary = await _create_summary(auth_client, auth_headers)
    resp = await auth_client.get("/api/v1/history/summaries", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total_items"] >= 1
    ids = [item["id"] for item in data["items"]]
    assert summary["id"] in ids


# ── GET /api/v1/history/summaries/{id} ────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_summary_by_id(auth_client, auth_headers):
    created = await _create_summary(auth_client, auth_headers)
    resp = await auth_client.get(
        f"/api/v1/history/summaries/{created['id']}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_summary_not_found(auth_client, auth_headers):
    resp = await auth_client.get(
        f"/api/v1/history/summaries/{uuid.uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


# ── DELETE /api/v1/history/summaries/{id} ─────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_summary(auth_client, auth_headers):
    created = await _create_summary(auth_client, auth_headers)
    resp = await auth_client.delete(
        f"/api/v1/history/summaries/{created['id']}", headers=auth_headers
    )
    assert resp.status_code == 204

    # Confirm it's gone
    resp2 = await auth_client.get(
        f"/api/v1/history/summaries/{created['id']}", headers=auth_headers
    )
    assert resp2.status_code == 404
