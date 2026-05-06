"""Chat service — orchestrates session management, history, and AI replies."""

from __future__ import annotations

from typing import Optional

from app.ai.prompts import build_chat_prompt, CHAT_SYSTEM_PROMPT_GENERIC
from app.ai.router import route_chat
from app.db.repositories.chat_repository import ChatRepository
from app.db.repositories.summary_repository import SummaryRepository

MAX_HISTORY_MESSAGES = 10
MAX_CONTEXT_CHARS = 8000


def _auto_title(first_message: str) -> str:
    words = first_message.strip().split()
    title = " ".join(words[:8])
    return title[:252] + "..." if len(title) > 255 else title[:255]


async def handle_chat(
    *,
    db,
    user_id: str,
    message: str,
    session_id: Optional[str] = None,
    summary_id: Optional[str] = None,
) -> dict:
    """
    Handle one round of chat.

    - Creates a new session if *session_id* is None.
    - Injects document context from *summary_id* if provided.
    - Persists both user message and assistant reply.

    Returns dict with session_id, message_id, reply, tokens_used, created_at.
    """
    repo = ChatRepository(db)

    # Resolve or create session
    if session_id:
        session = await repo.get_session(session_id, user_id)
        if not session:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Chat session not found")
        # Use existing session's summary_id if none provided
        if summary_id is None:
            summary_id = session.get("summary_id")
    else:
        title = _auto_title(message)
        session = await repo.create_session(
            user_id=user_id, title=title, summary_id=summary_id
        )
        session_id = session["id"]

    # Build message list for AI
    messages: list[dict] = []

    # System prompt with optional document context
    if summary_id:
        summary_record = await SummaryRepository(db).get_by_id(summary_id, user_id)
        if summary_record:
            system_content = build_chat_prompt(
                summary=summary_record["summary"],
                original_text=summary_record.get("original_text", "")[:MAX_CONTEXT_CHARS],
            )
        else:
            system_content = CHAT_SYSTEM_PROMPT_GENERIC
    else:
        system_content = CHAT_SYSTEM_PROMPT_GENERIC

    messages.append({"role": "system", "content": system_content})

    # Inject recent history
    history = await repo.get_recent_messages(session_id, limit=MAX_HISTORY_MESSAGES)
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Append new user message
    messages.append({"role": "user", "content": message})

    # Call AI
    ai_result = await route_chat(messages)
    reply_text: str = ai_result["text"]
    tokens_used: int | None = ai_result.get("tokens_used")

    # Persist user message then assistant reply
    await repo.create_message(session_id, "user", message)
    assistant_row = await repo.create_message(
        session_id, "assistant", reply_text, tokens_used
    )
    await repo.update_session_timestamp(session_id)

    return {
        "session_id": session_id,
        "message_id": assistant_row["id"],
        "reply": reply_text,
        "tokens_used": tokens_used,
        "created_at": assistant_row["created_at"],
    }
