from sqlalchemy import Column, String, Boolean

from app.db.models.base import Base, TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = uuid_pk()
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
