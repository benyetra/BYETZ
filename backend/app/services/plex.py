import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

PLEX_API_BASE = "https://plex.tv/api/v2"


class PlexService:
    def __init__(self):
        self.headers = {
            "X-Plex-Client-Identifier": settings.plex_client_id,
            "X-Plex-Product": settings.plex_product,
            "Accept": "application/json",
        }

    async def validate_token(self, token: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{PLEX_API_BASE}/user",
                    headers={**self.headers, "X-Plex-Token": token},
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("id"),
                        "username": data.get("username"),
                        "email": data.get("email"),
                        "thumb": data.get("thumb"),
                    }
            except httpx.RequestError:
                pass
        return None

    async def get_servers(self, token: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{PLEX_API_BASE}/resources",
                    headers={**self.headers, "X-Plex-Token": token},
                    params={"includeHttps": 1, "includeRelay": 0},
                )
                if response.status_code == 200:
                    resources = response.json()
                    servers = []
                    for r in resources:
                        if r.get("provides") == "server":
                            connections = r.get("connections", [])
                            local = next(
                                (c for c in connections if c.get("local")),
                                connections[0] if connections else None,
                            )
                            if local:
                                servers.append({
                                    "server_id": r["clientIdentifier"],
                                    "name": r["name"],
                                    "address": local["address"],
                                    "port": local["port"],
                                    "is_reachable": r.get("presence", False),
                                    "token": r.get("accessToken", token),
                                })
                    return servers
            except httpx.RequestError:
                pass
        return []

    async def get_libraries(self, server_url: str, token: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{server_url}/library/sections",
                    headers={**self.headers, "X-Plex-Token": token},
                )
                if response.status_code == 200:
                    data = response.json()
                    libraries = []
                    for section in data.get("MediaContainer", {}).get("Directory", []):
                        if section.get("type") in ("movie", "show"):
                            libraries.append({
                                "library_key": section["key"],
                                "title": section["title"],
                                "library_type": section["type"],
                                "total_items": section.get("count", 0),
                            })
                    return libraries
            except httpx.RequestError:
                pass
        return []

    async def get_library_items(
        self, server_url: str, token: str, library_key: str, library_type: str = "movie",
    ) -> list[dict]:
        """Fetch processable items from a Plex library.
        For movie libraries: returns movies directly.
        For show libraries: returns episodes (type=4) so we get actual file paths."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # For show libraries, fetch episodes directly (type=4)
                # Shows themselves don't have file paths — episodes do
                url = f"{server_url}/library/sections/{library_key}/all"
                params = {}
                if library_type == "show":
                    params["type"] = "4"  # Plex type 4 = episode

                response = await client.get(
                    url,
                    headers={**self.headers, "X-Plex-Token": token},
                    params=params,
                )
                if response.status_code == 200:
                    data = response.json()
                    items = []
                    for item in data.get("MediaContainer", {}).get("Metadata", []):
                        media = item.get("Media", [{}])
                        if not media:
                            continue
                        parts = media[0].get("Part", [{}])
                        file_path = parts[0].get("file") if parts else None
                        if not file_path:
                            continue

                        # For episodes, build a combined title
                        title = item.get("grandparentTitle", item["title"])
                        season_episode = None
                        if item.get("type") == "episode":
                            s = item.get("parentIndex", 0)
                            e = item.get("index", 0)
                            season_episode = f"S{s:02d}E{e:02d}"
                            ep_title = item.get("title", "")
                            title = f"{item.get('grandparentTitle', title)} - {season_episode} - {ep_title}"

                        items.append({
                            "rating_key": item["ratingKey"],
                            "title": title,
                            "type": item["type"],
                            "year": item.get("year") or item.get("parentYear"),
                            "genres": [g["tag"] for g in item.get("Genre", [])],
                            "actors": [r["tag"] for r in item.get("Role", [])[:5]],
                            "director": next((d["tag"] for d in item.get("Director", [])), None),
                            "duration": item.get("duration"),
                            "poster": item.get("thumb") or item.get("grandparentThumb"),
                            "content_rating": item.get("contentRating"),
                            "file_path": file_path,
                            "season_episode": season_episode,
                        })
                    return items
            except httpx.RequestError:
                pass
        return []
