from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PlexServer(BaseModel):
    server_id: str
    name: str
    address: str
    port: int
    is_reachable: bool


class PlexLibraryInfo(BaseModel):
    library_key: str
    title: str
    library_type: str
    total_items: int


class LibraryDetail(BaseModel):
    id: UUID
    library_title: str
    library_type: str
    enabled: bool
    total_items: int
    processed_items: int
    processing_percentage: float
    last_scanned: Optional[datetime] = None


class LibraryStatus(BaseModel):
    server_name: str
    server_reachable: bool
    libraries: list[LibraryDetail]


class LibraryToggle(BaseModel):
    library_id: UUID
    enabled: bool


class TasteProfileTitle(BaseModel):
    media_id: str
    title: str
    year: Optional[int] = None
    poster_url: Optional[str] = None
    genre_tags: list[str] = []
    media_type: str


class TasteProfileSelection(BaseModel):
    selections: list[TasteProfileTitle]
