"""History endpoints: list/get/delete summaries and list chat sessions."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.core.limiter import limiter
from app.db.repositories.chat_repository import ChatRepository
from app.db.repositories.summary_repository import SummaryRepository
from app.schemas.chat import ChatSessionListItem, ChatSessionListResponse
from app.schemas.summarize import PaginationMeta, SummaryListResponse, SummaryResponse
from fastapi import Request
import math

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/summaries", response_model=SummaryListResponse)
@limiter.limit("60/minute")
async def list_summaries(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    source_type: Optional[str] = Query(None, pattern="^(text|pdf)$"),
    keyword: Optional[str] = Query(None, min_length=1, max_length=100),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> SummaryListResponse:
    """Paginated list of the authenticated user's summaries."""
    repo = SummaryRepository(db)
    items, total = await repo.list_by_user(
        str(current_user["id"]),
        page=page,
        page_size=page_size,
        source_type=source_type,
        keyword=keyword,
    )
    total_pages = math.ceil(total / page_size) if total else 0
    return SummaryListResponse(
        items=[SummaryResponse(**item) for item in items],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
@limiter.limit("60/minute")
async def get_summary(
    request: Request,
    summary_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> SummaryResponse:
    """Get a single summary by ID."""
    repo = SummaryRepository(db)
    record = await repo.get_by_id(summary_id, str(current_user["id"]))
    if not record:
        raise NotFoundError("Summary not found")
    return SummaryResponse(**record)


@router.delete("/summaries/{summary_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_summary(
    request: Request,
    summary_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> None:
    """Delete a summary."""
    repo = SummaryRepository(db)
    deleted = await repo.delete(summary_id, str(current_user["id"]))
    if not deleted:
        raise NotFoundError("Summary not found")


@router.get("/chats", response_model=ChatSessionListResponse)
@limiter.limit("60/minute")
async def list_chat_sessions(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ChatSessionListResponse:
    """Paginated list of the user's chat sessions."""
    repo = ChatRepository(db)
    items, total = await repo.list_sessions(
        str(current_user["id"]), page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total else 0
    return ChatSessionListResponse(
        items=[ChatSessionListItem(**item) for item in items],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )
