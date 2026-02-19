import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        database_url="sqlite+aiosqlite:///test.db",
        database_url_sync="sqlite:///test.db",
        redis_url="redis://localhost:6379/1",
        secret_key="test-secret-key",
        clip_storage_path="/tmp/test-clips",
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_clip_id():
    return uuid4()
