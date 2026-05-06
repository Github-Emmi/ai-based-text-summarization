"""Unit tests for pdf_service."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import PDFExtractionError
from app.services.pdf_service import extract_text_from_pdf


def _make_pdf_bytes(text_per_page: list[str | None]) -> bytes:
    """Build minimal fake PDF bytes (just for type; we mock pdfplumber)."""
    return b"%PDF-1.4 fake"


@pytest.mark.asyncio
async def test_extracts_text_from_pages():
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Hello from page one."
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Hello from page two."

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page1, mock_page2]

    with patch("pdfplumber.open", return_value=mock_pdf):
        result = await extract_text_from_pdf(b"%PDF-1.4 fake")

    assert "Hello from page one." in result
    assert "Hello from page two." in result


@pytest.mark.asyncio
async def test_skips_none_pages():
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = None
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Real text here."

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page1, mock_page2]

    with patch("pdfplumber.open", return_value=mock_pdf):
        result = await extract_text_from_pdf(b"%PDF fake")

    assert result == "Real text here."


@pytest.mark.asyncio
async def test_raises_when_no_text_extracted():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf):
        with pytest.raises(PDFExtractionError):
            await extract_text_from_pdf(b"%PDF fake")


@pytest.mark.asyncio
async def test_raises_when_empty_pages():
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = []

    with patch("pdfplumber.open", return_value=mock_pdf):
        with pytest.raises(PDFExtractionError):
            await extract_text_from_pdf(b"%PDF fake")


@pytest.mark.asyncio
async def test_strips_whitespace():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "   some text   "

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf):
        result = await extract_text_from_pdf(b"%PDF fake")

    assert result == "some text"
