from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.interaction import Interaction
from app.models.clip import Clip
from app.models.user import UserEmbedding
from app.schemas.interaction import InteractionCreate, InteractionResponse


class InteractionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_interaction(self, user_id: UUID, data: InteractionCreate) -> InteractionResponse:
        interaction = Interaction(
            user_id=user_id,
            clip_id=data.clip_id,
            action=data.action.value,
            watch_duration_ms=data.watch_duration_ms,
            session_id=data.session_id,
        )
        self.db.add(interaction)
        await self._update_user_embedding(user_id, data)
        await self.db.commit()
        await self.db.refresh(interaction)

        return InteractionResponse(
            id=interaction.id,
            clip_id=interaction.clip_id,
            action=interaction.action,
            created_at=str(interaction.created_at),
        )

    async def _update_user_embedding(self, user_id: UUID, data: InteractionCreate):
        result = await self.db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        )
        user_emb = result.scalar_one_or_none()
        if not user_emb:
            return

        clip_result = await self.db.execute(select(Clip).where(Clip.id == data.clip_id))
        clip = clip_result.scalar_one_or_none()
        if not clip:
            return

        weights = {
            "like": {"clip": 1.0, "title": 0.3, "genre": 0.1},
            "dislike": {"clip": -1.0, "title": -0.2, "genre": -0.05},
            "save": {"clip": 1.5, "title": 0.4, "genre": 0.15},
            "skip": {"clip": -0.3, "title": 0.0, "genre": 0.0},
            "watch_complete": {"clip": 0.5, "title": 0.1, "genre": 0.05},
        }

        action_weights = weights.get(data.action.value, {"clip": 0, "title": 0, "genre": 0})

        genre_weights = user_emb.genre_weights or {}
        for genre in (clip.genre_tags or []):
            current = genre_weights.get(genre, 0.0)
            genre_weights[genre] = current + action_weights["genre"]

        user_emb.genre_weights = genre_weights
        user_emb.interaction_count = (user_emb.interaction_count or 0) + 1
