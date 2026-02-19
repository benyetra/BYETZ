from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.clip import FeedResponse
from app.services.auth import get_current_user
from app.services.recommendation import RecommendationService

router = APIRouter()


@router.get("", response_model=FeedResponse)
async def get_feed(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec_service = RecommendationService(db)
    clips = await rec_service.get_personalized_feed(user_id, limit=limit, offset=offset)
    return FeedResponse(clips=clips, offset=offset, limit=limit, has_more=len(clips) == limit)
