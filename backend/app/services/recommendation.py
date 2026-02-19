import random
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, not_
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
        self, user_id: UUID, limit: int = 10, offset: int = 0,
    ) -> list[ClipResponse]:
        user_emb = await self._get_user_embedding(user_id)
        is_cold_start = (user_emb.interaction_count or 0) < settings.cold_start_threshold

        disliked_ids = await self._get_disliked_clip_ids(user_id)
        recent_liked_ids = await self._get_recent_liked_ids(user_id, days=7)
        exclude_ids = set(disliked_ids) | set(recent_liked_ids)

        if is_cold_start:
            clips = await self._cold_start_feed(user_id, exclude_ids, limit, offset)
        else:
            clips = await self._personalized_feed(user_id, user_emb, exclude_ids, limit, offset)

        clips = self._apply_composition_rules(clips)
        return [self._clip_to_response(c) for c in clips[:limit]]

    async def _cold_start_feed(
        self, user_id: UUID, exclude_ids: set, limit: int, offset: int,
    ) -> list[Clip]:
        taste_result = await self.db.execute(
            select(TasteSelection.media_id).where(TasteSelection.user_id == user_id)
        )
        taste_media_ids = [r[0] for r in taste_result.all()]

        query = select(Clip).where(Clip.is_active == True)
        if exclude_ids:
            query = query.where(not_(Clip.id.in_(exclude_ids)))

        if taste_media_ids:
            taste_clips_q = query.where(Clip.media_id.in_(taste_media_ids)).order_by(
                Clip.composite_score.desc()
            ).limit(limit)
            taste_result = await self.db.execute(taste_clips_q)
            taste_clips = list(taste_result.scalars().all())

            remaining = limit - len(taste_clips)
            if remaining > 0:
                used_ids = {c.id for c in taste_clips} | exclude_ids
                other_q = query.where(
                    not_(Clip.media_id.in_(taste_media_ids)),
                )
                if used_ids:
                    other_q = other_q.where(not_(Clip.id.in_(used_ids)))
                other_q = other_q.order_by(Clip.composite_score.desc()).limit(remaining)
                other_result = await self.db.execute(other_q)
                taste_clips.extend(other_result.scalars().all())
            return taste_clips
        else:
            result = await self.db.execute(
                query.order_by(Clip.composite_score.desc()).offset(offset).limit(limit)
            )
            return list(result.scalars().all())

    async def _personalized_feed(
        self, user_id: UUID, user_emb: UserEmbedding,
        exclude_ids: set, limit: int, offset: int,
    ) -> list[Clip]:
        fetch_limit = limit * 3
        query = select(Clip).where(Clip.is_active == True)
        if exclude_ids:
            query = query.where(not_(Clip.id.in_(exclude_ids)))
        query = query.order_by(Clip.composite_score.desc()).limit(fetch_limit)

        result = await self.db.execute(query)
        candidates = list(result.scalars().all())
        genre_weights = user_emb.genre_weights or {}

        scored = []
        for clip in candidates:
            base_score = clip.composite_score or 0.0
            genre_boost = sum(genre_weights.get(g, 0.0) for g in (clip.genre_tags or []))
            genre_boost = min(genre_boost, 0.5)

            recency_boost = 0.0
            if clip.created_at and (datetime.utcnow() - clip.created_at).days < 2:
                recency_boost = 0.2

            scored.append((clip, base_score + genre_boost + recency_boost))

        scored.sort(key=lambda x: x[1], reverse=True)

        exploration_count = max(1, int(limit * settings.exploration_rate))
        main_count = limit - exploration_count
        main_clips = [c for c, _ in scored[:main_count]]

        remaining = [c for c, _ in scored[main_count:]]
        explore_clips = random.sample(remaining, min(exploration_count, len(remaining))) if remaining else []

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
