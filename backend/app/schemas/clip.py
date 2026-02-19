from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ClipResponse(BaseModel):
    id: UUID
    media_id: str
    title: str
    season_episode: Optional[str] = None
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    composite_score: float
    genre_tags: list[str] = []
    actors: list[str] = []
    director: Optional[str] = None
    decade: Optional[str] = None
    mood_tags: list[str] = []
    thumbnail_url: Optional[str] = None
    stream_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    clips: list[ClipResponse]
    offset: int
    limit: int
    has_more: bool
