"""Main summarization service.

Orchestrates: pre-processing → AI call → keyword extraction → DB persistence.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from app.ai.prompts import build_summarize_prompt
from app.ai.router import route_summarize
from app.db.repositories.summary_repository import SummaryRepository
from app.services.keyword_extractor import extract_keywords
from app.services.preprocessor import count_words, detect_language


async def summarize_and_save(
    *,
    db,
    user_id: str,
    text: str,
    summary_length: str = "medium",
    format: str = "paragraph",
    source_type: str = "text",
    original_filename: Optional[str] = None,
) -> dict:
    """
    Summarize *text*, extract keywords, and persist to the summaries table.

    Returns the newly created summary record dict.
    """
    input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    language = detect_language(text)

    # Truncate to ~50 000 chars (~12 500 tokens) to stay within LLM context limits.
    # Large PDFs can produce hundreds of thousands of chars otherwise.
    _MAX_AI_CHARS = 50_000
    ai_text = text[:_MAX_AI_CHARS]

    system_prompt = build_summarize_prompt(format=format, length=summary_length)
    ai_result = await route_summarize(system_prompt=system_prompt, text=ai_text)

    summary_text: str = ai_result["text"]
    model_used: str = ai_result["model"]
    tokens_used: Optional[int] = ai_result.get("tokens_used")

    keywords = extract_keywords(text)
    word_count = count_words(summary_text)

    repo = SummaryRepository(db)
    record = await repo.create(
        user_id=user_id,
        input_hash=input_hash,
        original_text=text,
        summary=summary_text,
        format=format,
        summary_length=summary_length,
        word_count=word_count,
        language=language,
        model_used=model_used,
        tokens_used=tokens_used,
        keywords=keywords,
        source_type=source_type,
        original_filename=original_filename,
    )
    return record
