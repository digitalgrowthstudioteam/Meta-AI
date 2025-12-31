import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User

from app.meta_api.oauth import build_meta_oauth_url
from app.meta_api.service import MetaOAuthService
from app.meta_api.schemas import MetaConnectResponse

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/connect", response_model=MetaConnectResponse)
async def connect_meta_account(
    current_user: User = Depends(get_current_user),
):
    state = str(uuid.uuid4())
    redirect_url = build_meta_oauth_url(state)

    return {"redirect_url": redirect_url}


@router.get("/oauth/callback")
async def meta_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await MetaOAuthService.store_token(
            db=db,
            user_id=current_user.id,
            code=code,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Meta OAuth failed")

    return {"status": "Meta account connected successfully"}
