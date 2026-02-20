from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import engine, Base
from app.models import user, clip, interaction  # noqa: F401 — ensure models are registered
from app.routers import auth, feed, clips, interactions, profile, library
from app.routers import settings as settings_router
from app.routers import taste_profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Your Personal Clip Feed - powered by Plex",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(feed.router, prefix="/feed", tags=["Feed"])
app.include_router(clips.router, prefix="/clips", tags=["Clips"])
app.include_router(interactions.router, prefix="/interactions", tags=["Interactions"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(library.router, prefix="/library", tags=["Library"])
app.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
app.include_router(taste_profile.router, prefix="/taste-profile", tags=["Taste Profile"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}
