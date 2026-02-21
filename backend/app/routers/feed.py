from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.clip import FeedRequest, FeedResponse
from app.services.auth import get_current_user
from app.services.recommendation import RecommendationService

router = APIRouter()


@router.post("", response_model=FeedResponse)
async def get_feed(
    body: FeedRequest,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec_service = RecommendationService(db)
    clips = await rec_service.get_personalized_feed(
        user_id, limit=body.limit, seen_ids=set(body.seen_ids),
    )
    return FeedResponse(clips=clips, has_more=len(clips) == body.limit)


# Keep GET for backwards compat / simple testing
@router.get("", response_model=FeedResponse)
async def get_feed_get(
    limit: int = Query(default=20, ge=1, le=50),
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rec_service = RecommendationService(db)
    clips = await rec_service.get_personalized_feed(user_id, limit=limit, seen_ids=set())
    return FeedResponse(clips=clips, has_more=len(clips) == limit)
