"""Chat endpoints: POST /chat, GET /chat/{session_id}, DELETE /chat/{session_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.core.limiter import limiter
from app.db.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatMessageItem,
    ChatReplyResponse,
    ChatRequest,
    ChatSessionDetailResponse,
)
from app.services.chat_service import handle_chat
from fastapi import Request

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatReplyResponse, status_code=200)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ChatReplyResponse:
    """Send a message and get an AI reply."""
    result = await handle_chat(
        db=db,
        user_id=str(current_user["id"]),
        message=body.message,
        session_id=body.session_id,
        summary_id=body.summary_id,
    )
    return ChatReplyResponse(**result)


@router.get("/{session_id}", response_model=ChatSessionDetailResponse)
@limiter.limit("60/minute")
async def get_session(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ChatSessionDetailResponse:
    """Retrieve full chat history for a session."""
    repo = ChatRepository(db)
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise NotFoundError("Chat session not found")
    messages = await repo.get_messages(session_id)
    return ChatSessionDetailResponse(
        session_id=session["id"],
        title=session.get("title"),
        summary_id=session.get("summary_id"),
        messages=[ChatMessageItem(**m) for m in messages],
        created_at=session["created_at"],
    )


@router.delete("/{session_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_session(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> None:
    """Delete a chat session and all its messages."""
    repo = ChatRepository(db)
    deleted = await repo.delete_session(session_id, str(current_user["id"]))
    if not deleted:
        raise NotFoundError("Chat session not found")
