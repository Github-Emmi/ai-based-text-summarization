"""Text pre-processing utilities: language detection, word counting."""

from __future__ import annotations


def count_words(text: str) -> int:
    """Return approximate word count."""
    return len(text.split())


def detect_language(text: str) -> str:
    """
    Detect language of *text*.

    Uses ``langdetect`` when available; falls back to 'en' otherwise.
    langdetect is an optional dependency — not installed by default.
    """
    try:
        from langdetect import detect, LangDetectException  # type: ignore[import]
        try:
            return detect(text[:1000])
        except LangDetectException:
            return "en"
    except ImportError:
        return "en"
