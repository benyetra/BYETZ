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

    async def get_library_items(self, server_url: str, token: str, library_key: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{server_url}/library/sections/{library_key}/all",
                    headers={**self.headers, "X-Plex-Token": token},
                )
                if response.status_code == 200:
                    data = response.json()
                    items = []
                    for item in data.get("MediaContainer", {}).get("Metadata", []):
                        media = item.get("Media", [{}])[0]
                        parts = media.get("Part", [{}])
                        file_path = parts[0].get("file") if parts else None
                        items.append({
                            "rating_key": item["ratingKey"],
                            "title": item["title"],
                            "type": item["type"],
                            "year": item.get("year"),
                            "genres": [g["tag"] for g in item.get("Genre", [])],
                            "actors": [r["tag"] for r in item.get("Role", [])[:5]],
                            "director": next((d["tag"] for d in item.get("Director", [])), None),
                            "duration": item.get("duration"),
                            "poster": item.get("thumb"),
                            "content_rating": item.get("contentRating"),
                            "file_path": file_path,
                        })
                    return items
            except httpx.RequestError:
                pass
        return []
