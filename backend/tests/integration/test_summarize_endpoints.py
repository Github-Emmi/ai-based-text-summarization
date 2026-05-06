"""Integration tests for summarization endpoints.

Tests mock the AI layer so no real OpenAI key is needed.
DB is required (docker-compose up -d).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


LONG_TEXT = (
    "Artificial intelligence (AI) is intelligence demonstrated by machines, "
    "as opposed to natural intelligence displayed by animals including humans. "
    "AI research has been defined as the field of study of intelligent agents, "
    "which refers to any system that perceives its environment and takes actions "
    "that maximize its chance of achieving its goals. The term 'artificial "
    "intelligence' had previously been used to describe machines that mimic and "
    "display human cognitive skills associated with the human mind, such as "
    "learning and problem-solving. This definition has since been rejected by "
    "major AI researchers who now describe AI in terms of rationality and acting "
    "rationally, which does not limit how intelligence can be articulated. "
    "AI applications include advanced web search engines, recommendation systems, "
    "understanding human speech, self-driving cars, generative or creative tools, "
    "and competing at the highest level in strategic games. "
) * 3  # ~600 chars × 3 to exceed 50-char minimum comfortably


MOCK_AI_RESULT = {
    "text": "AI is intelligence shown by machines used in many applications.",
    "model": "gpt-4o-mini",
    "tokens_used": 50,
}


# ── POST /api/v1/summarize/text ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_text_success(auth_client, auth_headers):
    with patch(
        "app.services.summarizer.route_summarize",
        new_callable=AsyncMock,
        return_value=MOCK_AI_RESULT,
    ):
        resp = await auth_client.post(
            "/api/v1/summarize/text",
            json={"text": LONG_TEXT, "summary_length": "short", "format": "paragraph"},
            headers=auth_headers,
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["summary"] == MOCK_AI_RESULT["text"]
    assert data["model_used"] == "gpt-4o-mini"
    assert data["source_type"] == "text"
    assert isinstance(data["keywords"], list)
    assert data["id"]


@pytest.mark.asyncio
async def test_summarize_text_too_short(auth_client, auth_headers):
    resp = await auth_client.post(
        "/api/v1/summarize/text",
        json={"text": "short"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_summarize_text_requires_auth(auth_client):
    resp = await auth_client.post(
        "/api/v1/summarize/text",
        json={"text": LONG_TEXT},
    )
    # FastAPI HTTPBearer returns 403 when no header; our handler normalises to 401
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_summarize_pdf_wrong_mime(auth_client, auth_headers):
    resp = await auth_client.post(
        "/api/v1/summarize/pdf",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "INVALID_FILE_TYPE"
