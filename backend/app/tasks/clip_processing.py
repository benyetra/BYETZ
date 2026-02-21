import os
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models.clip import Clip, MediaItem, PlexLibrary
from app.models.user import User
from app.services.clip_engine import ClipEngine
from app.services.scoring import ClipScoringService
from app.services.plex import PlexService

settings = get_settings()

sync_engine = create_engine(settings.database_url_sync)
SyncSession = sessionmaker(bind=sync_engine)

# Overlap threshold: if a candidate's midpoint is within this range of an
# existing clip's midpoint, consider it a duplicate (in ms)
OVERLAP_THRESHOLD_MS = 5000


def _existing_clip_midpoints(db, media_id: str) -> list[int]:
    """Get midpoints of all existing clips for a media item."""
    result = db.execute(
        select(Clip.start_time_ms, Clip.end_time_ms).where(
            Clip.media_id == media_id, Clip.is_active == True
        )
    )
    return [(row[0] + row[1]) // 2 for row in result.all()]


def _overlaps_existing(candidate_start: int, candidate_end: int, existing_midpoints: list[int]) -> bool:
    """Check if a candidate overlaps with any existing clip."""
    candidate_mid = (candidate_start + candidate_end) // 2
    for mid in existing_midpoints:
        if abs(candidate_mid - mid) < OVERLAP_THRESHOLD_MS:
            return True
    return False


@celery_app.task(bind=True, max_retries=3)
def process_media_item(self, media_item_id: str):
    db = SyncSession()
    item = None
    try:
        item = db.execute(
            select(MediaItem).where(MediaItem.id == uuid.UUID(media_item_id))
        ).scalar_one_or_none()

        if not item or not item.file_path:
            return {"status": "skipped", "reason": "item not found or no file path"}

        # Check if file is accessible
        if not os.path.exists(item.file_path):
            item.processing_status = "pending"
            db.commit()
            return {"status": "skipped", "reason": f"file not accessible: {item.file_path}"}

        # --- Diff check: how many clips do we already have? ---
        max_clips = settings.clips_per_movie if item.media_type == "movie" else settings.clips_per_episode
        existing_count = db.execute(
            select(func.count()).select_from(Clip).where(
                Clip.media_id == item.plex_rating_key, Clip.is_active == True
            )
        ).scalar() or 0

        if existing_count >= max_clips:
            # Already have enough clips — mark completed and skip
            item.processing_status = "completed"
            item.clips_generated = existing_count
            item.last_processed = datetime.utcnow()
            db.commit()
            return {"status": "skipped", "reason": f"already has {existing_count}/{max_clips} clips"}

        clips_needed = max_clips - existing_count
        existing_midpoints = _existing_clip_midpoints(db, item.plex_rating_key)

        item.processing_status = "processing"
        db.commit()

        engine = ClipEngine()
        scoring = ClipScoringService()

        subtitles = engine.extract_subtitles(item.file_path)
        scene_changes = engine.detect_scene_changes(item.file_path)
        audio_energy = engine.analyze_audio_energy(item.file_path)

        total_duration = item.duration_ms or 7200000
        candidates = engine.identify_clip_candidates(
            subtitles, scene_changes, audio_energy, total_duration,
        )

        # Filter out candidates that overlap with existing clips
        if existing_midpoints:
            candidates = [
                c for c in candidates
                if not _overlaps_existing(c.start_ms, c.end_ms, existing_midpoints)
            ]

        # Rank and take only what we need
        ranked = scoring.rank_candidates(candidates, clips_needed)

        clips_dir = os.path.join(settings.clip_storage_path, str(item.plex_rating_key))
        os.makedirs(clips_dir, exist_ok=True)

        clips_created = 0
        for candidate in ranked:
            clip_id = uuid.uuid4()
            clip_path = os.path.join(clips_dir, f"{clip_id}.mp4")

            success = engine.extract_clip(
                item.file_path, clip_path, candidate.start_ms, candidate.end_ms,
            )

            if success:
                thumb_dir = os.path.join(clips_dir, str(clip_id))
                mid_point = candidate.start_ms + (candidate.duration_ms // 2)
                thumbs = engine.generate_thumbnails(
                    item.file_path, thumb_dir,
                    [candidate.start_ms, mid_point, candidate.end_ms - 1000],
                )
                decade = f"{(item.year // 10) * 10}s" if item.year else None
                embedding = scoring.generate_content_embedding(
                    item.genre_tags or [], item.actors or [],
                    item.director or "", decade or "",
                    {"quote_match": candidate.quote_match_score,
                     "audio_energy": candidate.audio_energy_score},
                )
                composite = scoring.compute_composite_score(candidate)

                clip = Clip(
                    id=clip_id, media_id=item.plex_rating_key, title=item.title,
                    start_time_ms=candidate.start_ms, end_time_ms=candidate.end_ms,
                    duration_ms=candidate.duration_ms, file_path=clip_path,
                    thumbnail_paths=thumbs, composite_score=composite,
                    quote_match_score=candidate.quote_match_score,
                    audio_energy_score=candidate.audio_energy_score,
                    scene_composition_score=candidate.scene_composition_score,
                    dialogue_density_score=candidate.dialogue_density_score,
                    temporal_position_score=candidate.temporal_position_score,
                    genre_tags=item.genre_tags, actors=item.actors,
                    director=item.director, decade=decade, embedding=embedding,
                )
                db.add(clip)
                clips_created += 1

        total_clips = existing_count + clips_created
        item.processing_status = "completed"
        item.clips_generated = total_clips
        item.last_processed = datetime.utcnow()

        db.commit()
        return {
            "status": "completed",
            "clips_created": clips_created,
            "clips_existing": existing_count,
            "clips_total": total_clips,
        }

    except Exception as exc:
        db.rollback()
        if item:
            item.processing_status = "failed"
            db.commit()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task
def discover_libraries(user_id: str):
    """Phase 1: Discover Plex libraries and create PlexLibrary records.
    Auto-disables libraries with '4K' or 'UHD' in the title."""
    db = SyncSession()
    try:
        user = db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        ).scalar_one_or_none()
        if not user:
            return {"status": "error", "reason": "user not found"}

        plex_service = PlexService()
        loop = asyncio.new_event_loop()
        servers = loop.run_until_complete(plex_service.get_servers(user.plex_token))

        libraries_found = 0
        for server in servers:
            server_token = server.get("token", user.plex_token)
            server_url = f"http://{server['address']}:{server['port']}"
            libraries = loop.run_until_complete(
                plex_service.get_libraries(server_url, server_token)
            )

            for lib_info in libraries:
                plex_lib = db.execute(
                    select(PlexLibrary).where(
                        PlexLibrary.server_id == server["server_id"],
                        PlexLibrary.library_key == lib_info["library_key"],
                    )
                ).scalar_one_or_none()

                title = lib_info["title"]
                is_4k = any(tag in title.upper() for tag in ["4K", "UHD", "2160"])
                if not plex_lib:
                    plex_lib = PlexLibrary(
                        server_id=server["server_id"],
                        server_name=server["name"],
                        library_key=lib_info["library_key"],
                        library_title=title,
                        library_type=lib_info["library_type"],
                        total_items=lib_info.get("total_items", 0),
                        enabled=not is_4k,
                    )
                    db.add(plex_lib)
                else:
                    plex_lib.total_items = lib_info.get("total_items", 0)
                    plex_lib.last_scanned = datetime.utcnow()

                libraries_found += 1

        loop.close()
        db.commit()
        return {"status": "completed", "libraries_found": libraries_found}
    except Exception as exc:
        db.rollback()
        return {"status": "error", "reason": str(exc)}
    finally:
        db.close()


@celery_app.task
def scan_library(user_id: str):
    """Phase 2: Process only enabled libraries — fetch items and queue clip generation.
    Commits items to DB first, THEN queues Celery tasks so workers can find them.

    Diff-aware: only queues items that need clips generated. Skips items that
    already have the expected number of clips. Recovers stuck 'processing' items.
    """
    db = SyncSession()
    try:
        user = db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        ).scalar_one_or_none()
        if not user:
            return {"status": "error", "reason": "user not found"}

        plex_service = PlexService()
        loop = asyncio.new_event_loop()
        servers = loop.run_until_complete(plex_service.get_servers(user.plex_token))

        # Get enabled libraries from DB
        enabled_libs = db.execute(
            select(PlexLibrary).where(PlexLibrary.enabled == True)
        ).scalars().all()
        enabled_keys = {(lib.server_id, lib.library_key) for lib in enabled_libs}

        # Recover stuck items: reset "processing" items older than 2 hours
        stale_cutoff = datetime.utcnow() - timedelta(hours=2)
        stale_items = db.execute(
            select(MediaItem).where(
                MediaItem.processing_status == "processing",
                MediaItem.last_processed < stale_cutoff,
            )
        ).scalars().all()
        for stale in stale_items:
            stale.processing_status = "pending"

        # Also reset items stuck in "processing" with no last_processed timestamp
        stuck_items = db.execute(
            select(MediaItem).where(
                MediaItem.processing_status == "processing",
                MediaItem.last_processed == None,
            )
        ).scalars().all()
        for stuck in stuck_items:
            stuck.processing_status = "pending"

        if stale_items or stuck_items:
            db.commit()

        # Phase 1: Collect all items and save to DB
        item_ids_to_process = []
        items_skipped = 0
        items_new = 0

        for server in servers:
            server_token = server.get("token", user.plex_token)
            server_url = f"http://{server['address']}:{server['port']}"
            libraries = loop.run_until_complete(
                plex_service.get_libraries(server_url, server_token)
            )

            for lib_info in libraries:
                key = (server["server_id"], lib_info["library_key"])
                if key not in enabled_keys:
                    continue

                plex_lib = db.execute(
                    select(PlexLibrary).where(
                        PlexLibrary.server_id == server["server_id"],
                        PlexLibrary.library_key == lib_info["library_key"],
                    )
                ).scalar_one_or_none()

                if plex_lib:
                    plex_lib.total_items = lib_info.get("total_items", 0)
                    plex_lib.last_scanned = datetime.utcnow()

                # Fetch items — pass library_type so episodes are fetched for shows
                items = loop.run_until_complete(
                    plex_service.get_library_items(
                        server_url, server_token, lib_info["library_key"],
                        library_type=lib_info["library_type"],
                    )
                )

                for item_data in items:
                    existing = db.execute(
                        select(MediaItem).where(
                            MediaItem.plex_rating_key == item_data["rating_key"]
                        )
                    ).scalar_one_or_none()

                    if not existing:
                        # Brand new item
                        media_item = MediaItem(
                            plex_rating_key=item_data["rating_key"],
                            title=item_data["title"], media_type=item_data["type"],
                            year=item_data.get("year"), genre_tags=item_data.get("genres", []),
                            actors=item_data.get("actors", []),
                            director=item_data.get("director"),
                            duration_ms=item_data.get("duration"),
                            poster_url=item_data.get("poster"),
                            content_rating=item_data.get("content_rating"),
                            file_path=item_data.get("file_path"),
                        )
                        db.add(media_item)
                        db.flush()
                        item_ids_to_process.append(str(media_item.id))
                        items_new += 1

                    elif existing.processing_status in ("pending", "failed"):
                        # Retry failed/pending items
                        item_ids_to_process.append(str(existing.id))

                    elif existing.processing_status == "completed":
                        # Check if we need more clips (diff check)
                        max_clips = (
                            settings.clips_per_movie
                            if existing.media_type == "movie"
                            else settings.clips_per_episode
                        )
                        actual_clips = db.execute(
                            select(func.count()).select_from(Clip).where(
                                Clip.media_id == existing.plex_rating_key,
                                Clip.is_active == True,
                            )
                        ).scalar() or 0

                        if actual_clips < max_clips:
                            # Need more clips — re-queue
                            existing.processing_status = "pending"
                            item_ids_to_process.append(str(existing.id))
                        else:
                            items_skipped += 1

                # Update processed count
                if plex_lib:
                    processed = db.execute(
                        select(func.count()).select_from(MediaItem).where(
                            MediaItem.processing_status == "completed",
                        )
                    ).scalar() or 0
                    plex_lib.processed_items = processed

        loop.close()

        # Commit all items to DB BEFORE queuing tasks
        db.commit()

        # Phase 2: Now queue tasks — workers will find committed items
        for item_id in item_ids_to_process:
            process_media_item.delay(item_id)

        return {
            "status": "completed",
            "items_queued": len(item_ids_to_process),
            "items_new": items_new,
            "items_skipped": items_skipped,
            "items_recovered": len(stale_items) + len(stuck_items),
        }
    except Exception as exc:
        db.rollback()
        return {"status": "error", "reason": str(exc)}
    finally:
        db.close()
