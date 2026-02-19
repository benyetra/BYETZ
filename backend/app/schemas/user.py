from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PlexAuthRequest(BaseModel):
    plex_token: str


class PlexAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    username: str


class UserProfile(BaseModel):
    id: UUID
    plex_username: str
    plex_email: Optional[str] = None
    plex_thumb: Optional[str] = None
    total_likes: int = 0
    total_saves: int = 0
    total_clips_watched: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    subtitle_overlay: Optional[bool] = None
    content_maturity_filter: Optional[str] = None
    clip_quality: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    subtitle_overlay: bool = False
    content_maturity_filter: str = "all"
    clip_quality: str = "1080p"
    notifications_enabled: bool = True

    model_config = {"from_attributes": True}
