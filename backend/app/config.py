from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "BYETZ"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://byetz:byetz@localhost:5432/byetz"
    database_url_sync: str = "postgresql://byetz:byetz@localhost:5432/byetz"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Plex
    plex_client_id: str = "byetz-app"
    plex_product: str = "BYETZ"

    # Clip Storage
    clip_storage_path: str = "/data/clips"

    # Clip settings
    min_clip_duration_ms: int = 8000
    max_clip_duration_ms: int = 30000
    clips_per_movie: int = 10
    clips_per_episode: int = 5

    # Recommendation
    exploration_rate: float = 0.20
    max_consecutive_same_title: int = 2
    max_genre_ratio: float = 0.40
    cold_start_threshold: int = 50

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    model_config = {"env_prefix": "BYETZ_", "env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
