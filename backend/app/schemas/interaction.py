from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"
    SKIP = "skip"
    WATCH_COMPLETE = "watch_complete"


class InteractionCreate(BaseModel):
    clip_id: UUID
    action: ActionType
    watch_duration_ms: Optional[int] = None
    session_id: Optional[UUID] = None


class InteractionResponse(BaseModel):
    id: UUID
    clip_id: UUID
    action: str
    created_at: str

    model_config = {"from_attributes": True}
