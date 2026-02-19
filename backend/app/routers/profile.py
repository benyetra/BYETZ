from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.user import UserProfile
from app.schemas.clip import ClipResponse
from app.services.auth import get_current_user
from app.services.profile import ProfileService

router = APIRouter()


@router.get("", response_model=UserProfile)
async def get_profile(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.get_profile(user_id)


@router.get("/saved", response_model=list[ClipResponse])
async def get_saved_clips(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.get_saved_clips(user_id)
