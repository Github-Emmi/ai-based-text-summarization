"""AI router — tries multiple free OpenRouter models, then HuggingFace fallback."""

from __future__ import annotations

import openai

from app.ai.openai_client import openai_complete, openai_chat
from app.ai.huggingface_client import hf_api_complete
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
import logging

logger = logging.getLogger(__name__)

# Free OpenRouter models with active endpoints (verified 2026-05).
# Primary model from settings is always tried first.
# These span different providers so rate limits are independent.
_OPENROUTER_FALLBACK_MODELS = [
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-4b-it:free",
]


async def route_summarize(
    system_prompt: str,
    text: str,
    max_tokens: int = 1024,
) -> dict:
    """Try the configured model first, then rotate free fallbacks, then HuggingFace."""
    if settings.OPENAI_API_KEY:
        # Build ordered model list: primary first, then fallbacks (deduped)
        primary = settings.OPENAI_MODEL
        models_to_try = [primary] + [
            m for m in _OPENROUTER_FALLBACK_MODELS if m != primary
        ]

        for model in models_to_try:
            _err: str | None = None
            try:
                result = await openai_complete(system_prompt, text, max_tokens, model=model)
                logger.info(
                    f"Summarization via OpenRouter model '{model}': {result['tokens_used']} tokens"
                )
                return result
            except openai.RateLimitError as exc:
                _err = str(exc)
                logger.warning(f"Model '{model}' rate-limited, trying next: {_err[:120]}")
            except openai.APIError as exc:
                _err = str(exc)
                logger.warning(f"Model '{model}' API error, trying next: {_err[:120]}")

        logger.warning("All OpenRouter free models exhausted, falling back to HuggingFace")

    # Final fallback — HuggingFace Inference API
    _hf_err: str | None = None
    try:
        result = await hf_api_complete(text)
        logger.info(f"Summarization via HuggingFace fallback: {result['model']}")
        return result
    except Exception as exc:
        _hf_err = str(exc)
    if _hf_err is not None:
        logger.error(f"HuggingFace fallback also failed: {_hf_err}")

    raise AIServiceUnavailableError()


async def route_chat(messages: list[dict], max_tokens: int = 1024) -> dict:
    """Chat completion — rotates free OpenRouter models same as summarize."""
    if settings.OPENAI_API_KEY:
        primary = settings.OPENAI_MODEL
        models_to_try = [primary] + [
            m for m in _OPENROUTER_FALLBACK_MODELS if m != primary
        ]

        for model in models_to_try:
            _err: str | None = None
            try:
                result = await openai_chat(messages, max_tokens, model=model)
                return result
            except openai.RateLimitError as exc:
                _err = str(exc)
                logger.warning(f"Chat model '{model}' rate-limited, trying next: {_err[:120]}")
            except openai.APIError as exc:
                _err = str(exc)
                logger.warning(f"Chat model '{model}' API error, trying next: {_err[:120]}")

    raise AIServiceUnavailableError("No available AI model for chat")
