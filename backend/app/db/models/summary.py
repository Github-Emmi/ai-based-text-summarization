from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.models.base import Base, TimestampMixin, uuid_pk


class Summary(Base, TimestampMixin):
    __tablename__ = "summaries"

    id = uuid_pk()
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input_hash = Column(String(64), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    format = Column(String(20), nullable=False, default="paragraph")
    summary_length = Column(String(10), nullable=False, default="medium")
    word_count = Column(Integer)
    language = Column(String(10))
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    keywords = Column(JSONB, default=list)
    source_type = Column(String(10), nullable=False, default="text")
    original_filename = Column(String(255))
