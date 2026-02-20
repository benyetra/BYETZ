from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.clip import PlexLibrary
from app.models.user import User
from app.schemas.library import LibraryStatus, LibraryDetail
from app.services.plex import PlexService


class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_status(self, user_id: UUID) -> LibraryStatus:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        libs_result = await self.db.execute(select(PlexLibrary))
        libraries = libs_result.scalars().all()

        details = []
        for lib in libraries:
            pct = (lib.processed_items / lib.total_items * 100) if lib.total_items > 0 else 0
            details.append(LibraryDetail(
                id=lib.id, library_title=lib.library_title,
                library_type=lib.library_type, enabled=lib.enabled,
                total_items=lib.total_items, processed_items=lib.processed_items,
                processing_percentage=round(pct, 1), last_scanned=lib.last_scanned,
            ))

        plex_service = PlexService()
        server_reachable = False
        server_name = "Unknown"
        if user and user.plex_token:
            servers = await plex_service.get_servers(user.plex_token)
            if servers:
                server_name = servers[0]["name"]
                server_reachable = servers[0]["is_reachable"]

        return LibraryStatus(
            server_name=server_name, server_reachable=server_reachable, libraries=details,
        )

    async def discover(self, user_id: UUID):
        from app.tasks.clip_processing import discover_libraries
        discover_libraries.delay(str(user_id))

    async def trigger_rescan(self, user_id: UUID):
        from app.tasks.clip_processing import scan_library
        scan_library.delay(str(user_id))

    async def toggle_library(self, library_id: UUID, enabled: bool):
        await self.db.execute(
            update(PlexLibrary).where(PlexLibrary.id == library_id).values(enabled=enabled)
        )
        await self.db.commit()
