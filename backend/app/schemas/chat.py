"""Pydantic schemas for chat endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ── Requests ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    summary_id: Optional[str] = None


# ── Responses ─────────────────────────────────────────────────────────────────

class ChatReplyResponse(BaseModel):
    session_id: str
    message_id: str
    reply: str
    tokens_used: Optional[int] = None
    created_at: datetime


class ChatMessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ChatSessionDetailResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    summary_id: Optional[str] = None
    messages: List[ChatMessageItem]
    created_at: datetime


class ChatSessionListItem(BaseModel):
    id: str
    title: Optional[str] = None
    summary_id: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    items: List[ChatSessionListItem]
    pagination: "PaginationMeta"


from app.schemas.summarize import PaginationMeta  # noqa: E402 — circular-safe
ChatSessionListResponse.model_rebuild()
