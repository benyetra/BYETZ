from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.services.auth import get_current_user
from app.services.interaction import InteractionService

router = APIRouter()


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction: InteractionCreate,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InteractionService(db)
    return await service.record_interaction(user_id, interaction)
