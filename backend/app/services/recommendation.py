import random
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, not_, func
from app.models.clip import Clip
from app.models.interaction import Interaction
from app.models.user import UserEmbedding, TasteSelection
from app.schemas.clip import ClipResponse
from app.config import get_settings

settings = get_settings()


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_personalized_feed(
        self, user_id: UUID, limit: int = 20, seen_ids: set[UUID] | None = None,
    ) -> list[ClipResponse]:
        seen_ids = seen_ids or set()
        user_emb = await self._get_user_embedding(user_id)
        is_cold_start = (user_emb.interaction_count or 0) < settings.cold_start_threshold

        disliked_ids = await self._get_disliked_clip_ids(user_id)
        recent_liked_ids = await self._get_recent_liked_ids(user_id, days=7)
        exclude_ids = set(disliked_ids) | set(recent_liked_ids) | seen_ids

        if is_cold_start:
            clips = await self._cold_start_feed(user_id, user_emb, exclude_ids, limit)
        else:
            clips = await self._personalized_feed(user_id, user_emb, exclude_ids, limit)

        clips = self._apply_composition_rules(clips)
        return [self._clip_to_response(c) for c in clips[:limit]]

    async def _cold_start_feed(
        self, user_id: UUID, user_emb: UserEmbedding,
        exclude_ids: set, limit: int,
    ) -> list[Clip]:
        """Cold start: use onboarding genre weights + taste selections + randomness."""
        genre_weights = user_emb.genre_weights or {}

        # Get taste selection media IDs for bonus scoring
        taste_result = await self.db.execute(
            select(TasteSelection.media_id).where(TasteSelection.user_id == user_id)
        )
        taste_media_ids = {r[0] for r in taste_result.all()}

        # Fetch a large candidate pool
        pool_size = limit * 8
        query = select(Clip).where(Clip.is_active == True)
        if exclude_ids:
            query = query.where(not_(Clip.id.in_(exclude_ids)))
        query = query.order_by(func.random()).limit(pool_size)

        result = await self.db.execute(query)
        candidates = list(result.scalars().all())

        if not candidates:
            return []

        # Score each clip
        scored = []
        for clip in candidates:
            score = 0.0

            # Base quality score (normalized to 0-1 range)
            base = clip.composite_score or 0.0
            score += min(base, 1.0) * 0.4

            # Genre match boost from onboarding weights
            if genre_weights and clip.genre_tags:
                genre_boost = sum(genre_weights.get(g, 0.0) for g in clip.genre_tags)
                score += min(max(genre_boost, -0.3), 0.5)

            # Taste selection bonus — clips from media the user selected
            if clip.media_id in taste_media_ids:
                score += 0.3

            # Random factor to prevent determinism
            score += random.uniform(0, 0.35)

            scored.append((clip, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Take top candidates with exploration mix
        exploration_count = max(2, int(limit * settings.exploration_rate))
        main_count = limit - exploration_count
        main_clips = [c for c, _ in scored[:main_count]]

        remaining = [c for c, _ in scored[main_count:]]
        explore_clips = random.sample(
            remaining, min(exploration_count, len(remaining))
        ) if remaining else []

        feed = main_clips + explore_clips
        random.shuffle(feed)
        return feed

    async def _personalized_feed(
        self, user_id: UUID, user_emb: UserEmbedding,
        exclude_ids: set, limit: int,
    ) -> list[Clip]:
        """Warm feed: genre weights from interactions + exploration."""
        pool_size = limit * 5
        query = select(Clip).where(Clip.is_active == True)
        if exclude_ids:
            query = query.where(not_(Clip.id.in_(exclude_ids)))
        # Use random ordering for the candidate pool to get variety
        query = query.order_by(func.random()).limit(pool_size)

        result = await self.db.execute(query)
        candidates = list(result.scalars().all())
        genre_weights = user_emb.genre_weights or {}

        scored = []
        for clip in candidates:
            score = 0.0

            # Base quality score
            base = clip.composite_score or 0.0
            score += min(base, 1.0) * 0.35

            # Genre match from learned weights
            if genre_weights and clip.genre_tags:
                genre_boost = sum(genre_weights.get(g, 0.0) for g in clip.genre_tags)
                score += min(max(genre_boost, -0.3), 0.5)

            # Recency boost for fresh clips
            if clip.created_at and (datetime.utcnow() - clip.created_at).days < 2:
                score += 0.15

            # Small random factor for variety
            score += random.uniform(0, 0.2)

            scored.append((clip, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        exploration_count = max(2, int(limit * settings.exploration_rate))
        main_count = limit - exploration_count
        main_clips = [c for c, _ in scored[:main_count]]

        remaining = [c for c, _ in scored[main_count:]]
        explore_clips = random.sample(
            remaining, min(exploration_count, len(remaining))
        ) if remaining else []

        feed = main_clips + explore_clips
        random.shuffle(feed)
        return feed

    def _apply_composition_rules(self, clips: list[Clip]) -> list[Clip]:
        result = []
        title_streak = {}
        genre_counts: dict[str, int] = {}
        total = 0

        for clip in clips:
            title = clip.title
            consec = title_streak.get(title, 0)
            if consec >= settings.max_consecutive_same_title:
                continue

            clip_genres = clip.genre_tags or []
            skip_genre = False
            for genre in clip_genres:
                if total > 0 and (genre_counts.get(genre, 0) / total) > settings.max_genre_ratio:
                    skip_genre = True
                    break
            if skip_genre:
                continue

            result.append(clip)
            title_streak = {k: (v + 1 if k == title else 0) for k, v in title_streak.items()}
            if title not in title_streak:
                title_streak[title] = 1

            for genre in clip_genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            total += 1

        return result

    async def _get_user_embedding(self, user_id: UUID) -> UserEmbedding:
        result = await self.db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        )
        emb = result.scalar_one_or_none()
        if not emb:
            emb = UserEmbedding(
                user_id=user_id, embedding=[0.0] * 64,
                genre_weights={}, interaction_count=0,
            )
        return emb

    async def _get_disliked_clip_ids(self, user_id: UUID) -> list[UUID]:
        result = await self.db.execute(
            select(Interaction.clip_id).where(
                Interaction.user_id == user_id, Interaction.action == "dislike",
            )
        )
        return [r[0] for r in result.all()]

    async def _get_recent_liked_ids(self, user_id: UUID, days: int = 7) -> list[UUID]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(Interaction.clip_id).where(
                Interaction.user_id == user_id,
                Interaction.action == "like",
                Interaction.created_at > cutoff,
            )
        )
        return [r[0] for r in result.all()]

    def _clip_to_response(self, clip: Clip) -> ClipResponse:
        return ClipResponse(
            id=clip.id, media_id=clip.media_id, title=clip.title,
            season_episode=clip.season_episode,
            start_time_ms=clip.start_time_ms, end_time_ms=clip.end_time_ms,
            duration_ms=clip.duration_ms, composite_score=clip.composite_score,
            genre_tags=clip.genre_tags or [], actors=clip.actors or [],
            director=clip.director, decade=clip.decade,
            mood_tags=clip.mood_tags or [],
            thumbnail_url=f"/clips/{clip.id}/thumbnail",
            stream_url=f"/clips/{clip.id}/stream",
            created_at=clip.created_at,
        )
