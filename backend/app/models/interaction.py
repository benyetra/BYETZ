import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ActionType(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"
    SKIP = "skip"
    WATCH_COMPLETE = "watch_complete"


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    watch_duration_ms = Column(Integer, nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    clip = relationship("Clip", back_populates="interactions")
