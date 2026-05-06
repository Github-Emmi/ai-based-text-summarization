"""Unit tests for chat_service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest

from app.services.chat_service import handle_chat, _auto_title


# ─── _auto_title ──────────────────────────────────────────────────────────────

class TestAutoTitle:
    def test_first_eight_words(self):
        msg = "one two three four five six seven eight nine ten"
        assert _auto_title(msg) == "one two three four five six seven eight"

    def test_short_message_unchanged(self):
        assert _auto_title("hello world") == "hello world"

    def test_truncates_at_255(self):
        msg = "word " * 100  # very long
        result = _auto_title(msg)
        assert len(result) <= 255

    def test_leading_whitespace_stripped(self):
        result = _auto_title("   hello world   ")
        assert not result.startswith(" ")


# ─── handle_chat ──────────────────────────────────────────────────────────────

def _make_session(session_id="sess-1", summary_id=None):
    return {"id": session_id, "summary_id": summary_id, "title": "Test"}


def _make_message_row(msg_id="msg-1", content="reply", role="assistant"):
    return {
        "id": msg_id,
        "role": role,
        "content": content,
        "tokens_used": 50,
        "created_at": datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc),
    }


@pytest.mark.asyncio
async def test_creates_new_session_when_no_session_id():
    fake_ai = {"text": "AI reply here.", "model": "openrouter/free", "tokens_used": 42}
    new_session = _make_session("new-sess")
    assistant_row = _make_message_row("msg-new", "AI reply here.")

    with (
        patch("app.services.chat_service.route_chat", new=AsyncMock(return_value=fake_ai)),
        patch("app.services.chat_service.ChatRepository") as MockChatRepo,
        patch("app.services.chat_service.SummaryRepository"),
    ):
        mock_repo = MagicMock()
        mock_repo.create_session = AsyncMock(return_value=new_session)
        mock_repo.get_recent_messages = AsyncMock(return_value=[])
        mock_repo.create_message = AsyncMock(return_value=assistant_row)
        mock_repo.update_session_timestamp = AsyncMock()
        MockChatRepo.return_value = mock_repo

        result = await handle_chat(
            db=MagicMock(),
            user_id="user-1",
            message="Hello AI!",
        )

    assert result["session_id"] == "new-sess"
    assert result["reply"] == "AI reply here."
    mock_repo.create_session.assert_called_once()


@pytest.mark.asyncio
async def test_continues_existing_session():
    fake_ai = {"text": "Continued reply.", "model": "openrouter/free", "tokens_used": 30}
    existing_session = _make_session("existing-sess")
    assistant_row = _make_message_row("msg-cont", "Continued reply.")

    with (
        patch("app.services.chat_service.route_chat", new=AsyncMock(return_value=fake_ai)),
        patch("app.services.chat_service.ChatRepository") as MockChatRepo,
        patch("app.services.chat_service.SummaryRepository"),
    ):
        mock_repo = MagicMock()
        mock_repo.get_session = AsyncMock(return_value=existing_session)
        mock_repo.get_recent_messages = AsyncMock(return_value=[])
        mock_repo.create_message = AsyncMock(return_value=assistant_row)
        mock_repo.update_session_timestamp = AsyncMock()
        MockChatRepo.return_value = mock_repo

        result = await handle_chat(
            db=MagicMock(),
            user_id="user-1",
            message="Follow-up question.",
            session_id="existing-sess",
        )

    assert result["session_id"] == "existing-sess"
    mock_repo.create_session.assert_not_called()


@pytest.mark.asyncio
async def test_raises_not_found_for_missing_session():
    from app.core.exceptions import NotFoundError

    with patch("app.services.chat_service.ChatRepository") as MockChatRepo:
        mock_repo = MagicMock()
        mock_repo.get_session = AsyncMock(return_value=None)
        MockChatRepo.return_value = mock_repo

        with pytest.raises(NotFoundError):
            await handle_chat(
                db=MagicMock(),
                user_id="user-1",
                message="Hello?",
                session_id="ghost-session",
            )


@pytest.mark.asyncio
async def test_injects_summary_context_when_summary_id_given():
    fake_ai = {"text": "Context-aware reply.", "model": "openrouter/free", "tokens_used": 60}
    new_session = _make_session("ctx-sess", summary_id=None)
    assistant_row = _make_message_row("msg-ctx", "Context-aware reply.")
    summary_record = {
        "id": "sum-1",
        "summary": "Summary text here.",
        "original_text": "Full original doc text.",
    }

    with (
        patch("app.services.chat_service.route_chat", new=AsyncMock(return_value=fake_ai)),
        patch("app.services.chat_service.ChatRepository") as MockChatRepo,
        patch("app.services.chat_service.SummaryRepository") as MockSumRepo,
    ):
        mock_chat_repo = MagicMock()
        mock_chat_repo.create_session = AsyncMock(return_value=new_session)
        mock_chat_repo.get_recent_messages = AsyncMock(return_value=[])
        mock_chat_repo.create_message = AsyncMock(return_value=assistant_row)
        mock_chat_repo.update_session_timestamp = AsyncMock()
        MockChatRepo.return_value = mock_chat_repo

        mock_sum_repo = MagicMock()
        mock_sum_repo.get_by_id = AsyncMock(return_value=summary_record)
        MockSumRepo.return_value = mock_sum_repo

        result = await handle_chat(
            db=MagicMock(),
            user_id="user-1",
            message="Tell me about this document.",
            summary_id="sum-1",
        )

    mock_sum_repo.get_by_id.assert_called_once()
    assert result["reply"] == "Context-aware reply."


@pytest.mark.asyncio
async def test_persists_both_user_and_assistant_messages():
    fake_ai = {"text": "Both persisted.", "model": "openrouter/free", "tokens_used": 25}
    new_session = _make_session("persist-sess")
    assistant_row = _make_message_row("msg-persist", "Both persisted.")

    with (
        patch("app.services.chat_service.route_chat", new=AsyncMock(return_value=fake_ai)),
        patch("app.services.chat_service.ChatRepository") as MockChatRepo,
        patch("app.services.chat_service.SummaryRepository"),
    ):
        mock_repo = MagicMock()
        mock_repo.create_session = AsyncMock(return_value=new_session)
        mock_repo.get_recent_messages = AsyncMock(return_value=[])
        mock_repo.create_message = AsyncMock(return_value=assistant_row)
        mock_repo.update_session_timestamp = AsyncMock()
        MockChatRepo.return_value = mock_repo

        await handle_chat(
            db=MagicMock(),
            user_id="user-1",
            message="Persist me.",
        )

    # create_message called twice: user + assistant
    assert mock_repo.create_message.call_count == 2
    calls = mock_repo.create_message.call_args_list
    assert calls[0].args[1] == "user"
    assert calls[1].args[1] == "assistant"


@pytest.mark.asyncio
async def test_returns_tokens_used():
    fake_ai = {"text": "Token reply.", "model": "openrouter/free", "tokens_used": 77}
    new_session = _make_session("tok-sess")
    assistant_row = _make_message_row("msg-tok", "Token reply.")

    with (
        patch("app.services.chat_service.route_chat", new=AsyncMock(return_value=fake_ai)),
        patch("app.services.chat_service.ChatRepository") as MockChatRepo,
        patch("app.services.chat_service.SummaryRepository"),
    ):
        mock_repo = MagicMock()
        mock_repo.create_session = AsyncMock(return_value=new_session)
        mock_repo.get_recent_messages = AsyncMock(return_value=[])
        mock_repo.create_message = AsyncMock(return_value=assistant_row)
        mock_repo.update_session_timestamp = AsyncMock()
        MockChatRepo.return_value = mock_repo

        result = await handle_chat(
            db=MagicMock(),
            user_id="user-1",
            message="Token count test.",
        )

    assert result["tokens_used"] == 77
