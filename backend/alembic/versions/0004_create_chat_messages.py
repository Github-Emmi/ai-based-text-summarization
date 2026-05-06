"""create_chat_messages

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-29

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
    )
    op.create_index("idx_chat_messages_session_id", "chat_messages", ["session_id"])
    # ASC ordering index for retrieving conversation history in chronological order
    op.create_index(
        "idx_chat_messages_created_at", "chat_messages", [sa.text("created_at ASC")]
    )


def downgrade() -> None:
    op.drop_index("idx_chat_messages_created_at", table_name="chat_messages")
    op.drop_index("idx_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
