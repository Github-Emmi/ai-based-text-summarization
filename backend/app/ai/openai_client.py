"""OpenAI async client for summarization and chat completion."""

from __future__ import annotations

import openai
from openai import AsyncOpenAI

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kwargs: dict = {
            "api_key": settings.OPENAI_API_KEY,
            "timeout": 30.0,
            "max_retries": 2,
        }
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        _client = AsyncOpenAI(**kwargs)
    return _client


async def openai_complete(
    system_prompt: str,
    user_text: str,
    max_tokens: int = 1024,
    model: str | None = None,
) -> dict:
    """Call OpenAI chat completion and return {'text', 'model', 'tokens_used'}."""
    client = _get_client()
    _model = model or settings.OPENAI_MODEL
    response = await client.chat.completions.create(
        model=_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=max_tokens,
        temperature=settings.OPENAI_TEMPERATURE,
    )
    text = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else None
    return {
        "text": text,
        "model": _model,
        "tokens_used": tokens_used,
    }


async def openai_chat(messages: list[dict], max_tokens: int = 1024, model: str | None = None) -> dict:
    """Call OpenAI with a pre-built message list (for multi-turn chat)."""
    client = _get_client()
    _model = model or settings.OPENAI_MODEL
    response = await client.chat.completions.create(
        model=_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=settings.OPENAI_TEMPERATURE,
    )
    text = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else None
    return {
        "text": text,
        "model": _model,
        "tokens_used": tokens_used,
    }
