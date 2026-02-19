from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.library import TasteProfileTitle, TasteProfileSelection
from app.services.auth import get_current_user
from app.services.taste_profile import TasteProfileService

router = APIRouter()


@router.get("/titles", response_model=list[TasteProfileTitle])
async def get_titles(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TasteProfileService(db)
    return await service.get_available_titles(user_id)


@router.post("/select")
async def submit_selections(
    selection: TasteProfileSelection,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(selection.selections) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum 10 selections required",
        )
    service = TasteProfileService(db)
    await service.save_selections(user_id, selection.selections)
    return {"status": "taste_profile_saved", "count": len(selection.selections)}
