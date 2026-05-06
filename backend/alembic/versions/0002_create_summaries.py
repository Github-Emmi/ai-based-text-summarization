"""create_summaries

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-29

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "summaries",
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
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "format",
            sa.String(20),
            nullable=False,
            server_default="paragraph",
        ),
        sa.Column(
            "summary_length",
            sa.String(10),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("keywords", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "source_type",
            sa.String(10),
            nullable=False,
            server_default="text",
        ),
        sa.Column("original_filename", sa.String(255), nullable=True),
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
        sa.CheckConstraint("format IN ('paragraph', 'bullets')", name="ck_summaries_format"),
        sa.CheckConstraint(
            "summary_length IN ('short', 'medium', 'long')", name="ck_summaries_length"
        ),
        sa.CheckConstraint("source_type IN ('text', 'pdf')", name="ck_summaries_source_type"),
    )
    op.create_index("idx_summaries_user_id", "summaries", ["user_id"])
    op.create_index("idx_summaries_input_hash", "summaries", ["input_hash"])
    op.create_index(
        "idx_summaries_created_at", "summaries", [sa.text("created_at DESC")]
    )
    op.create_index(
        "idx_summaries_keywords",
        "summaries",
        ["keywords"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_summaries_keywords", table_name="summaries")
    op.drop_index("idx_summaries_created_at", table_name="summaries")
    op.drop_index("idx_summaries_input_hash", table_name="summaries")
    op.drop_index("idx_summaries_user_id", table_name="summaries")
    op.drop_table("summaries")
