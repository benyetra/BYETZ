from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, UserSettings
from app.models.interaction import Interaction
from app.models.clip import Clip
from app.schemas.user import UserProfile, UserSettingsUpdate, UserSettingsResponse
from app.schemas.clip import ClipResponse
from fastapi import HTTPException, status


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: UUID) -> UserProfile:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        likes = await self.db.execute(
            select(func.count()).select_from(Interaction).where(
                Interaction.user_id == user_id, Interaction.action == "like"
            )
        )
        saves = await self.db.execute(
            select(func.count()).select_from(Interaction).where(
                Interaction.user_id == user_id, Interaction.action == "save"
            )
        )
        total = await self.db.execute(
            select(func.count()).select_from(Interaction).where(Interaction.user_id == user_id)
        )

        return UserProfile(
            id=user.id, plex_username=user.plex_username,
            plex_email=user.plex_email, plex_thumb=user.plex_thumb,
            total_likes=likes.scalar() or 0, total_saves=saves.scalar() or 0,
            total_clips_watched=total.scalar() or 0, created_at=user.created_at,
        )

    async def get_saved_clips(self, user_id: UUID) -> list[ClipResponse]:
        result = await self.db.execute(
            select(Clip).join(Interaction, Interaction.clip_id == Clip.id).where(
                Interaction.user_id == user_id, Interaction.action == "save"
            ).order_by(Interaction.created_at.desc())
        )
        clips = result.scalars().all()
        return [
            ClipResponse(
                id=c.id, media_id=c.media_id, title=c.title,
                season_episode=c.season_episode,
                start_time_ms=c.start_time_ms, end_time_ms=c.end_time_ms,
                duration_ms=c.duration_ms, composite_score=c.composite_score,
                genre_tags=c.genre_tags or [], actors=c.actors or [],
                director=c.director, decade=c.decade, mood_tags=c.mood_tags or [],
                thumbnail_url=f"/clips/{c.id}/thumbnail",
                stream_url=f"/clips/{c.id}/stream", created_at=c.created_at,
            )
            for c in clips
        ]

    async def get_settings(self, user_id: UUID) -> UserSettingsResponse:
        result = await self.db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        s = result.scalar_one_or_none()
        if not s:
            s = UserSettings(user_id=user_id)
            self.db.add(s)
            await self.db.commit()
            await self.db.refresh(s)
        return UserSettingsResponse.model_validate(s)

    async def update_settings(self, user_id: UUID, update: UserSettingsUpdate) -> UserSettingsResponse:
        result = await self.db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        s = result.scalar_one_or_none()
        if not s:
            s = UserSettings(user_id=user_id)
            self.db.add(s)
        for key, value in update.model_dump(exclude_unset=True).items():
            setattr(s, key, value)
        await self.db.commit()
        await self.db.refresh(s)
        return UserSettingsResponse.model_validate(s)
