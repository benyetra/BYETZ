from datetime import datetime, timedelta
from uuid import UUID
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserEmbedding, UserSettings

security = HTTPBearer()
settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(self, plex_user: dict, plex_token: str) -> User:
        result = await self.db.execute(
            select(User).where(User.plex_user_id == str(plex_user["id"]))
        )
        user = result.scalar_one_or_none()

        if user:
            user.plex_token = plex_token
            user.plex_username = plex_user.get("username", user.plex_username)
            user.updated_at = datetime.utcnow()
        else:
            user = User(
                plex_user_id=str(plex_user["id"]),
                plex_username=plex_user.get("username", "Unknown"),
                plex_email=plex_user.get("email"),
                plex_thumb=plex_user.get("thumb"),
                plex_token=plex_token,
            )
            self.db.add(user)
            await self.db.flush()

            embedding = UserEmbedding(
                user_id=user.id,
                embedding=[0.0] * 64,
                genre_weights={},
            )
            self.db.add(embedding)

            user_settings = UserSettings(user_id=user.id)
            self.db.add(user_settings)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    def create_access_token(self, user_id: UUID) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_token(token: str) -> UUID:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            return UUID(user_id)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    return AuthService.decode_token(credentials.credentials)
