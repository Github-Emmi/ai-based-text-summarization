from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base, TimestampMixin, uuid_pk


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id = uuid_pk()
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # summary_id is nullable: a chat can exist without a linked summary.
    # ON DELETE SET NULL: deleting the summary does not cascade to the session.
    summary_id = Column(
        UUID(as_uuid=True),
        ForeignKey("summaries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False, default="New Chat")
