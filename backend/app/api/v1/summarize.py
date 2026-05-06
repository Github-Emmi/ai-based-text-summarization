"""Summarization endpoints: POST /summarize/text and POST /summarize/pdf."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from app.core.limiter import limiter
from app.schemas.summarize import SummarizeTextRequest, SummaryResponse
from app.services.pdf_service import extract_text_from_pdf
from app.services.summarizer import summarize_and_save
from fastapi import Request

router = APIRouter(prefix="/summarize", tags=["Summarization"])

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/text", response_model=SummaryResponse, status_code=200)
@limiter.limit("10/minute")
async def summarize_text(
    request: Request,
    body: SummarizeTextRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> SummaryResponse:
    """Summarize a raw text string."""
    record = await summarize_and_save(
        db=db,
        user_id=str(current_user["id"]),
        text=body.text,
        summary_length=body.summary_length,
        format=body.format,
        source_type="text",
    )
    return SummaryResponse(**record)


@router.post("/pdf", response_model=SummaryResponse, status_code=200)
@limiter.limit("5/minute")
async def summarize_pdf(
    request: Request,
    file: UploadFile = File(...),
    summary_length: str = Form("medium"),
    format: str = Form("paragraph"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> SummaryResponse:
    """Upload a PDF file and receive a summary."""
    # Validate MIME type
    if file.content_type != "application/pdf":
        raise InvalidFileTypeError("Only PDF files are accepted")

    # Read bytes and enforce size limit
    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_UPLOAD_BYTES:
        raise FileTooLargeError("File exceeds maximum size of 20MB")

    # Extract text
    text = await extract_text_from_pdf(pdf_bytes)

    record = await summarize_and_save(
        db=db,
        user_id=str(current_user["id"]),
        text=text,
        summary_length=summary_length,
        format=format,
        source_type="pdf",
        original_filename=file.filename,
    )
    return SummaryResponse(**record)
