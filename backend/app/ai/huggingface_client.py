"""HuggingFace Inference API client (no local model by default).

Only the Inference API mode is active unless ``USE_LOCAL_MODEL=true``.
Local pipeline mode requires ``transformers`` and is Python 3.14-compatible via
``run_in_executor``.
"""

from __future__ import annotations

import asyncio

import httpx

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

INFERENCE_URL = (
    f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
)


async def hf_api_complete(text: str, max_length: int = 150) -> dict:
    """Summarize *text* via the HuggingFace Inference API (free-tier)."""
    headers: dict[str, str] = {}
    if settings.HUGGINGFACE_API_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_API_TOKEN}"

    payload = {
        "inputs": text[:2048],  # BART context window is ~1024 tokens
        "parameters": {"max_length": max_length, "min_length": 40},
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        # HuggingFace returns 503 while the model warms up; retry up to 2 times.
        response = await client.post(INFERENCE_URL, headers=headers, json=payload)
        for attempt in range(2):
            if response.status_code != 503:
                break
            try:
                estimated = response.json().get("estimated_time", 20)
            except Exception:
                estimated = 20
            wait = min(float(estimated), 30.0)
            logger.warning(
                f"HuggingFace model loading (attempt {attempt + 1}/2), waiting {wait:.0f}s"
            )
            await asyncio.sleep(wait)
            response = await client.post(INFERENCE_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

    summary_text = result[0]["summary_text"] if isinstance(result, list) else result["generated_text"]
    return {
        "text": summary_text,
        "model": settings.HUGGINGFACE_MODEL,
        "tokens_used": None,
    }
