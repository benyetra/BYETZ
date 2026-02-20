import random
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.clip import MediaItem
from app.models.user import User, TasteSelection, UserEmbedding
from app.schemas.library import TasteProfileTitle
from app.services.plex import PlexService

SAMPLE_SIZE = 50


def _sample_genre_diverse(titles: list[TasteProfileTitle], n: int) -> list[TasteProfileTitle]:
    """Sample n titles ensuring all genres are represented."""
    if len(titles) <= n:
        random.shuffle(titles)
        return titles

    # Build genre -> titles mapping
    genre_buckets: dict[str, list[TasteProfileTitle]] = {}
    no_genre: list[TasteProfileTitle] = []
    for t in titles:
        if not t.genre_tags:
            no_genre.append(t)
        else:
            for g in t.genre_tags:
                genre_buckets.setdefault(g, []).append(t)

    # Shuffle each bucket
    for bucket in genre_buckets.values():
        random.shuffle(bucket)
    random.shuffle(no_genre)

    selected: list[TasteProfileTitle] = []
    selected_ids: set[str] = set()

    # Round-robin: pick one from each genre to guarantee coverage
    for genre in sorted(genre_buckets.keys()):
        for t in genre_buckets[genre]:
            if t.media_id not in selected_ids:
                selected.append(t)
                selected_ids.add(t.media_id)
                break
        if len(selected) >= n:
            break

    # Fill remaining slots randomly from all titles
    if len(selected) < n:
        remaining = [t for t in titles if t.media_id not in selected_ids]
        random.shuffle(remaining)
        for t in remaining:
            selected.append(t)
            selected_ids.add(t.media_id)
            if len(selected) >= n:
                break

    random.shuffle(selected)
    return selected


class TasteProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_titles(self, user_id: UUID) -> list[TasteProfileTitle]:
        # Check if we have media items in the database
        count_result = await self.db.execute(
            select(func.count()).select_from(MediaItem)
        )
        count = count_result.scalar() or 0

        if count > 0:
            titles = await self._titles_from_db()
        else:
            titles = await self._titles_from_plex(user_id)

        return _sample_genre_diverse(titles, SAMPLE_SIZE)

    async def _titles_from_db(self) -> list[TasteProfileTitle]:
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

    async def _titles_from_plex(self, user_id: UUID) -> list[TasteProfileTitle]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.plex_token:
            return []

        plex = PlexService()
        servers = await plex.get_servers(user.plex_token)
        if not servers:
            return []

        titles: list[TasteProfileTitle] = []
        seen_keys: set[str] = set()

        for server in servers:
            server_token = server.get("token", user.plex_token)
            server_url = f"http://{server['address']}:{server['port']}"

            libraries = await plex.get_libraries(server_url, server_token)

            for lib in libraries:
                items = await plex.get_library_items(
                    server_url, server_token, lib["library_key"]
                )
                for item in items:
                    key = item["rating_key"]
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    poster_url = None
                    if item.get("poster"):
                        poster_url = f"{server_url}{item['poster']}?X-Plex-Token={server_token}"

                    titles.append(TasteProfileTitle(
                        media_id=key,
                        title=item["title"],
                        year=item.get("year"),
                        poster_url=poster_url,
                        genre_tags=item.get("genres", []),
                        media_type=item.get("type", "movie"),
                    ))

        return titles

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
