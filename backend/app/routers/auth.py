from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import PlexAuthRequest, PlexAuthResponse
from app.services.plex import PlexService
from app.services.auth import AuthService

router = APIRouter()


@router.post("/plex", response_model=PlexAuthResponse)
async def authenticate_plex(
    request: PlexAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    plex_service = PlexService()
    plex_user = await plex_service.validate_token(request.plex_token)
    if not plex_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Plex token")

    auth_service = AuthService(db)
    user = await auth_service.get_or_create_user(plex_user, request.plex_token)
    access_token = auth_service.create_access_token(user.id)

    return PlexAuthResponse(
        access_token=access_token, user_id=user.id, username=user.plex_username,
    )
