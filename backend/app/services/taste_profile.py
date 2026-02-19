from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.clip import MediaItem
from app.models.user import TasteSelection, UserEmbedding
from app.schemas.library import TasteProfileTitle


class TasteProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_titles(self, user_id: UUID) -> list[TasteProfileTitle]:
        result = await self.db.execute(
            select(MediaItem).where(
                MediaItem.media_type.in_(["movie", "show"])
            ).order_by(MediaItem.title)
        )
        items = result.scalars().all()
        return [
            TasteProfileTitle(
                media_id=item.plex_rating_key, title=item.title,
                year=item.year, poster_url=item.poster_url,
                genre_tags=item.genre_tags or [], media_type=item.media_type,
            )
            for item in items
        ]

    async def save_selections(self, user_id: UUID, selections: list[TasteProfileTitle]):
        for sel in selections:
            self.db.add(TasteSelection(
                user_id=user_id, media_id=sel.media_id,
                title=sel.title, genre_tags=sel.genre_tags,
            ))

        genre_counts: dict[str, int] = {}
        for sel in selections:
            for genre in sel.genre_tags:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

        total = sum(genre_counts.values()) or 1
        genre_weights = {g: c / total for g, c in genre_counts.items()}

        result = await self.db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        )
        user_emb = result.scalar_one_or_none()
        if user_emb:
            user_emb.genre_weights = genre_weights

        await self.db.commit()
