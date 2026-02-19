from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import os
from app.database import get_db
from app.models.clip import Clip
from app.schemas.clip import ClipResponse
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/{clip_id}/stream")
async def stream_clip(
    clip_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    if not os.path.exists(clip.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip file not found")
    return FileResponse(clip.file_path, media_type="video/mp4", filename=f"{clip.id}.mp4")


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: UUID,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    return ClipResponse(
        id=clip.id, media_id=clip.media_id, title=clip.title,
        season_episode=clip.season_episode,
        start_time_ms=clip.start_time_ms, end_time_ms=clip.end_time_ms,
        duration_ms=clip.duration_ms, composite_score=clip.composite_score,
        genre_tags=clip.genre_tags or [], actors=clip.actors or [],
        director=clip.director, decade=clip.decade, mood_tags=clip.mood_tags or [],
        thumbnail_url=f"/clips/{clip.id}/thumbnail",
        stream_url=f"/clips/{clip.id}/stream", created_at=clip.created_at,
    )
