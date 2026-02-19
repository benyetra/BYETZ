import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plex_user_id = Column(String, unique=True, nullable=False, index=True)
    plex_username = Column(String, nullable=False)
    plex_email = Column(String)
    plex_thumb = Column(String)
    plex_token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user")
    embedding = relationship("UserEmbedding", back_populates="user", uselist=False)
    taste_selections = relationship("TasteSelection", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    embedding = Column(JSONB, nullable=False, default=list)
    genre_weights = Column(JSONB, nullable=False, default=dict)
    last_retrained = Column(DateTime, default=datetime.utcnow)
    interaction_count = Column(Integer, default=0)

    user = relationship("User", back_populates="embedding")


class TasteSelection(Base):
    __tablename__ = "taste_selections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    media_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    genre_tags = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="taste_selections")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    subtitle_overlay = Column(Boolean, default=False)
    content_maturity_filter = Column(String, default="all")
    clip_quality = Column(String, default="1080p")
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")
