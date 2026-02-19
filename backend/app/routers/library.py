from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
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
