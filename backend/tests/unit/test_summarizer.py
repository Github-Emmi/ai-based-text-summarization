"""Unit tests for summarizer service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.summarizer import summarize_and_save


def _make_db():
    """Return a minimal async DB connection mock."""
    return MagicMock()


@pytest.mark.asyncio
async def test_summarize_calls_route_summarize():
    fake_ai_result = {"text": "Short summary.", "model": "openrouter/free", "tokens_used": 50}
    fake_record = {"id": "uuid-1", "summary": "Short summary.", "keywords": ["summary"]}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        result = await summarize_and_save(
            db=_make_db(),
            user_id="user-1",
            text="This is a long enough text to be summarized by the AI service pipeline.",
        )

    assert result["summary"] == "Short summary."


@pytest.mark.asyncio
async def test_summarize_persists_to_repo():
    fake_ai_result = {"text": "Persisted summary.", "model": "gpt-4o", "tokens_used": 80}
    fake_record = {"id": "uuid-2", "summary": "Persisted summary.", "keywords": []}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        await summarize_and_save(
            db=_make_db(),
            user_id="user-2",
            text="Another long text that needs to be summarized by the AI service.",
        )

        mock_repo_instance.create.assert_called_once()
        call_kwargs = mock_repo_instance.create.call_args.kwargs
        assert call_kwargs["user_id"] == "user-2"
        assert call_kwargs["summary"] == "Persisted summary."


@pytest.mark.asyncio
async def test_summarize_passes_format_and_length():
    fake_ai_result = {"text": "Bullet summary.", "model": "openrouter/free", "tokens_used": 40}
    fake_record = {"id": "uuid-3", "summary": "Bullet summary.", "keywords": []}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        await summarize_and_save(
            db=_make_db(),
            user_id="user-3",
            text="Text that should be summarized in bullet format.",
            summary_length="short",
            format="bullets",
        )

        call_kwargs = mock_repo_instance.create.call_args.kwargs
        assert call_kwargs["format"] == "bullets"
        assert call_kwargs["summary_length"] == "short"


@pytest.mark.asyncio
async def test_summarize_records_model_and_tokens():
    fake_ai_result = {"text": "Model check.", "model": "openrouter/free", "tokens_used": 99}
    fake_record = {"id": "uuid-4", "summary": "Model check.", "keywords": []}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        await summarize_and_save(
            db=_make_db(),
            user_id="user-4",
            text="Checking that model and token count are passed through correctly.",
        )

        call_kwargs = mock_repo_instance.create.call_args.kwargs
        assert call_kwargs["model_used"] == "openrouter/free"
        assert call_kwargs["tokens_used"] == 99


@pytest.mark.asyncio
async def test_summarize_pdf_source_type():
    fake_ai_result = {"text": "PDF summary.", "model": "openrouter/free", "tokens_used": 60}
    fake_record = {"id": "uuid-5", "summary": "PDF summary.", "keywords": []}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        await summarize_and_save(
            db=_make_db(),
            user_id="user-5",
            text="PDF extracted text that is being summarized after extraction.",
            source_type="pdf",
            original_filename="report.pdf",
        )

        call_kwargs = mock_repo_instance.create.call_args.kwargs
        assert call_kwargs["source_type"] == "pdf"
        assert call_kwargs["original_filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_summarize_computes_input_hash():
    fake_ai_result = {"text": "Hash test.", "model": "openrouter/free", "tokens_used": 10}
    fake_record = {"id": "uuid-6", "summary": "Hash test.", "keywords": []}

    with (
        patch("app.services.summarizer.route_summarize", new=AsyncMock(return_value=fake_ai_result)),
        patch("app.services.summarizer.SummaryRepository") as MockRepo,
    ):
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(return_value=fake_record)
        MockRepo.return_value = mock_repo_instance

        await summarize_and_save(
            db=_make_db(),
            user_id="user-6",
            text="Consistent text for hashing purposes in the summarizer.",
        )

        call_kwargs = mock_repo_instance.create.call_args.kwargs
        # SHA-256 hex digest is always 64 chars
        assert len(call_kwargs["input_hash"]) == 64
