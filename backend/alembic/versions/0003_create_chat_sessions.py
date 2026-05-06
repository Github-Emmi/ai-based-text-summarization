"""create_chat_sessions

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-29

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # summary_id is nullable — ON DELETE SET NULL so deleting a summary
        # does not cascade to the chat session.
        sa.Column(
            "summary_id",
            UUID(as_uuid=True),
            sa.ForeignKey("summaries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False, server_default="New Chat"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("idx_chat_sessions_summary_id", "chat_sessions", ["summary_id"])


def downgrade() -> None:
    op.drop_index("idx_chat_sessions_summary_id", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
