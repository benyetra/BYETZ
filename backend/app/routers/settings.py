from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.user import UserSettingsUpdate, UserSettingsResponse
from app.services.auth import get_current_user
from app.services.profile import ProfileService

router = APIRouter()


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.get_settings(user_id)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    settings_update: UserSettingsUpdate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.update_settings(user_id, settings_update)
