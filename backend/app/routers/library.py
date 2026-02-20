from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import httpx
from app.database import get_db
from app.schemas.library import LibraryStatus, LibraryToggle
from app.services.auth import get_current_user
from app.services.library import LibraryService

router = APIRouter()


@router.get("/status", response_model=LibraryStatus)
async def get_library_status(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LibraryService(db)
    return await service.get_status(user_id)


@router.post("/discover")
async def discover_libraries(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Discover Plex libraries without processing. Auto-disables 4K/UHD libraries."""
    service = LibraryService(db)
    await service.discover(user_id)
    return {"status": "discovery_queued"}


@router.post("/process")
async def process_libraries(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process only enabled libraries."""
    service = LibraryService(db)
    await service.trigger_rescan(user_id)
    return {"status": "processing_queued"}


@router.post("/rescan")
async def trigger_rescan(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LibraryService(db)
    await service.trigger_rescan(user_id)
    return {"status": "rescan_queued"}


@router.put("/toggle")
async def toggle_library(
    toggle: LibraryToggle,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LibraryService(db)
    await service.toggle_library(toggle.library_id, toggle.enabled)
    return {"status": "updated"}


@router.get("/poster")
async def proxy_poster(
    url: str = Query(..., description="Plex poster URL to proxy"),
):
    """Proxy poster images from Plex so iOS clients don't need direct Plex access."""
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Plex returned error")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                iter([resp.content]),
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach Plex server")
