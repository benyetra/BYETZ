from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
import os
from app.database import get_db
from app.models.clip import Clip
from app.schemas.clip import ClipResponse
from app.services.auth import get_current_user, AuthService

router = APIRouter()


def _range_file_stream(file_path: str, start: int, end: int, chunk_size: int = 65536):
    """Generator that yields file chunks for a byte range."""
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.get("/{clip_id}/stream")
async def stream_clip(
    request: Request,
    clip_id: UUID,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Stream a clip with Range header support for AVPlayer."""
    if token:
        AuthService.decode_token(token)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token required")

    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")
    if not os.path.exists(clip.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip file not found")

    file_size = os.path.getsize(clip.file_path)
    range_header = request.headers.get("range")

    if range_header:
        # Parse Range: bytes=start-end
        range_spec = range_header.replace("bytes=", "").strip()
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        return StreamingResponse(
            _range_file_stream(clip.file_path, start, end),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )
    else:
        # Full file response
        return StreamingResponse(
            _range_file_stream(clip.file_path, 0, file_size - 1),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )


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
