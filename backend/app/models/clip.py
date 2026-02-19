import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Clip(Base):
    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    season_episode = Column(String, nullable=True)
    start_time_ms = Column(BigInteger, nullable=False)
    end_time_ms = Column(BigInteger, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    thumbnail_paths = Column(JSONB, default=list)
    composite_score = Column(Float, nullable=False, default=0.0)
    quote_match_score = Column(Float, default=0.0)
    audio_energy_score = Column(Float, default=0.0)
    scene_composition_score = Column(Float, default=0.0)
    dialogue_density_score = Column(Float, default=0.0)
    temporal_position_score = Column(Float, default=0.0)
    genre_tags = Column(JSONB, default=list)
    actors = Column(JSONB, default=list)
    director = Column(String, nullable=True)
    decade = Column(String, nullable=True)
    mood_tags = Column(JSONB, default=list)
    embedding = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="clip")


class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plex_rating_key = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    genre_tags = Column(JSONB, default=list)
    actors = Column(JSONB, default=list)
    director = Column(String, nullable=True)
    duration_ms = Column(BigInteger, nullable=True)
    poster_url = Column(String, nullable=True)
    content_rating = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    processing_status = Column(String, default="pending")
    clips_generated = Column(Integer, default=0)
    last_processed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlexLibrary(Base):
    __tablename__ = "plex_libraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(String, nullable=False)
    server_name = Column(String, nullable=False)
    library_key = Column(String, nullable=False)
    library_title = Column(String, nullable=False)
    library_type = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    last_scanned = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
