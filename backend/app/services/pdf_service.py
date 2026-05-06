"""PDF text extraction service using pdfplumber."""

from __future__ import annotations

import io

from app.core.exceptions import PDFExtractionError


async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.

    Raises ``PDFExtractionError`` if no text could be extracted.
    """
    try:
        import pdfplumber  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError("pdfplumber is not installed") from exc

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    extracted = "\n".join(text_parts).strip()
    if not extracted:
        raise PDFExtractionError()
    return extracted
