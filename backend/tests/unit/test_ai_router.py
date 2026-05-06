"""Unit tests for app/ai/router.py — route_summarize and route_chat."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import openai

from app.core.exceptions import AIServiceUnavailableError


# ─── route_summarize ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_route_summarize_uses_openai_when_key_set():
    fake_result = {"text": "Summary.", "model": "openrouter/free", "tokens_used": 50}

    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_complete", new=AsyncMock(return_value=fake_result)),
    ):
        mock_settings.OPENAI_API_KEY = "sk-test-key"

        from app.ai.router import route_summarize
        result = await route_summarize("System prompt", "User text")

    assert result["text"] == "Summary."


@pytest.mark.asyncio
async def test_route_summarize_falls_back_to_hf_on_openai_error():
    hf_result = {"text": "HF summary.", "model": "facebook/bart-large-cnn", "tokens_used": None}

    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_complete", new=AsyncMock(side_effect=openai.APIError("fail", request=None, body=None))),
        patch("app.ai.router.hf_api_complete", new=AsyncMock(return_value=hf_result)),
    ):
        mock_settings.OPENAI_API_KEY = "sk-test-key"

        from app.ai.router import route_summarize
        result = await route_summarize("System prompt", "User text")

    assert result["model"] == "facebook/bart-large-cnn"


@pytest.mark.asyncio
async def test_route_summarize_raises_when_both_fail():
    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_complete", new=AsyncMock(side_effect=openai.APIError("fail", request=None, body=None))),
        patch("app.ai.router.hf_api_complete", new=AsyncMock(side_effect=Exception("HF also down"))),
    ):
        mock_settings.OPENAI_API_KEY = "sk-test-key"

        from app.ai.router import route_summarize
        with pytest.raises(AIServiceUnavailableError):
            await route_summarize("System prompt", "User text")


@pytest.mark.asyncio
async def test_route_summarize_skips_openai_when_no_key():
    hf_result = {"text": "No key fallback.", "model": "facebook/bart-large-cnn", "tokens_used": None}

    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_complete", new=AsyncMock()) as mock_openai,
        patch("app.ai.router.hf_api_complete", new=AsyncMock(return_value=hf_result)),
    ):
        mock_settings.OPENAI_API_KEY = None

        from app.ai.router import route_summarize
        result = await route_summarize("System prompt", "User text")

    mock_openai.assert_not_called()
    assert result["text"] == "No key fallback."


# ─── route_chat ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_route_chat_returns_openai_result():
    fake_result = {"text": "Chat reply.", "model": "openrouter/free", "tokens_used": 30}
    messages = [{"role": "user", "content": "Hello"}]

    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_chat", new=AsyncMock(return_value=fake_result)),
    ):
        mock_settings.OPENAI_API_KEY = "sk-test-key"

        from app.ai.router import route_chat
        result = await route_chat(messages)

    assert result["text"] == "Chat reply."


@pytest.mark.asyncio
async def test_route_chat_raises_when_openai_fails():
    messages = [{"role": "user", "content": "Hello"}]

    with (
        patch("app.ai.router.settings") as mock_settings,
        patch("app.ai.router.openai_chat", new=AsyncMock(side_effect=openai.APIError("fail", request=None, body=None))),
    ):
        mock_settings.OPENAI_API_KEY = "sk-test-key"

        from app.ai.router import route_chat
        with pytest.raises(AIServiceUnavailableError):
            await route_chat(messages)


@pytest.mark.asyncio
async def test_route_chat_raises_when_no_key():
    messages = [{"role": "user", "content": "Hello"}]

    with patch("app.ai.router.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None

        from app.ai.router import route_chat
        with pytest.raises(AIServiceUnavailableError):
            await route_chat(messages)
