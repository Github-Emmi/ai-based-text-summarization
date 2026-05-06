from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base, uuid_pk


class ChatMessage(Base):
    """Chat messages do not need updated_at — messages are immutable once stored."""

    __tablename__ = "chat_messages"

    id = uuid_pk()
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
