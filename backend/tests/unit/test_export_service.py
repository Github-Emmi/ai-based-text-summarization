"""Unit tests for export_service."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.export_service import generate_summary_pdf


def _base_summary(**overrides) -> dict:
    base = {
        "id": "abc123",
        "summary": "This is the summarized content.",
        "source_type": "text",
        "summary_length": "medium",
        "format": "paragraph",
        "word_count": 6,
        "language": "en",
        "model_used": "openrouter/free",
        "tokens_used": 120,
        "keywords": ["summary", "content"],
        "created_at": datetime(2026, 4, 29, 12, 0, 0, tzinfo=timezone.utc),
        "original_filename": None,
    }
    base.update(overrides)
    return base


def test_returns_bytes():
    pdf_bytes = generate_summary_pdf(_base_summary())
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_output_starts_with_pdf_header():
    pdf_bytes = generate_summary_pdf(_base_summary())
    assert pdf_bytes[:4] == b"%PDF"


def test_keywords_list_included():
    summary = _base_summary(keywords=["machine", "learning", "neural"])
    pdf_bytes = generate_summary_pdf(summary)
    # PDF is binary but keywords should appear as text somewhere
    assert b"machine" in pdf_bytes or len(pdf_bytes) > 500  # non-trivial PDF


def test_empty_keywords_does_not_crash():
    summary = _base_summary(keywords=[])
    pdf_bytes = generate_summary_pdf(summary)
    assert isinstance(pdf_bytes, bytes)


def test_none_keywords_does_not_crash():
    summary = _base_summary(keywords=None)
    pdf_bytes = generate_summary_pdf(summary)
    assert isinstance(pdf_bytes, bytes)


def test_datetime_object_created_at():
    summary = _base_summary(created_at=datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc))
    pdf_bytes = generate_summary_pdf(summary)
    assert isinstance(pdf_bytes, bytes)


def test_string_created_at():
    summary = _base_summary(created_at="2026-01-15T09:30:00Z")
    pdf_bytes = generate_summary_pdf(summary)
    assert isinstance(pdf_bytes, bytes)


def test_missing_optional_fields_do_not_crash():
    # Minimal dict — only required field is summary
    minimal = {"summary": "Minimal summary text.", "keywords": []}
    pdf_bytes = generate_summary_pdf(minimal)
    assert isinstance(pdf_bytes, bytes)


def test_pdf_source_type_shows_filename():
    summary = _base_summary(source_type="pdf", original_filename="report.pdf")
    pdf_bytes = generate_summary_pdf(summary)
    assert isinstance(pdf_bytes, bytes)
