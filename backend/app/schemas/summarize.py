"""Pydantic schemas for summarization and history endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from typing import Literal


# ── Requests ──────────────────────────────────────────────────────────────────

class SummarizeTextRequest(BaseModel):
    text: str = Field(min_length=50, max_length=100_000)
    summary_length: Literal["short", "medium", "long"] = "medium"
    format: Literal["paragraph", "bullets"] = "paragraph"


# ── Responses ─────────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    id: str
    summary: str
    format: str
    summary_length: str
    word_count: Optional[int] = None
    language: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    keywords: List[str] = []
    source_type: str
    original_filename: Optional[str] = None
    created_at: datetime


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class SummaryListResponse(BaseModel):
    items: List[SummaryResponse]
    pagination: PaginationMeta
