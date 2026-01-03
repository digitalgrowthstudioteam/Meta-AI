import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User

from app.meta_api.oauth import build_meta_oauth_url
from app.meta_api.service import (
    MetaOAuthService,
    MetaAdAccountService,
    MetaCampaignService,
)
from app.meta_api.schemas import MetaConnectResponse
from app.meta_api.models import MetaOAuthState

router = APIRouter(prefix="/meta", tags=["Meta"])


# =========================================================
# DEV MODE USER RESOLUTION (TEMPORARY)
# =========================================================
async def get_dev_user(db: AsyncSession) -> Optional[User]:
    """
    Temporary user resolver while auth is disabled.
    Uses first available user in database.

    THIS WILL BE REMOVED when real auth is enabled.
    """
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none()


# ---------------------------------------------------------
# CONNECT META (OAUTH) — STATE CREATION (DEV SAFE)
# ---------------------------------------------------------
@router.get("/connect", response_model=MetaConnectResponse)
async def connect_meta_account(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)

    if not current_user:
        raise HTTPException(
            status_code=400,
            detail="No user available in development mode",
        )

    state = str(uuid.uuid4())

    oauth_state = MetaOAuthState(
        user_id=current_user.id,  # REAL UUID
        state=state,
    )

    db.add(oauth_state)
    await db.commit()

    redirect_url = build_meta_oauth_url(state)
    return {"redirect_url": redirect_url}


# ---------------------------------------------------------
# OAUTH CALLBACK — TOKEN + AUTO SYNC
# ---------------------------------------------------------
@router.get("/oauth/callback")
async def meta_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # 1️⃣ Validate OAuth state
    result = await db.execute(
        select(MetaOAuthState).where(
            MetaOAuthState.state == state,
            MetaOAuthState.is_used.is_(False),
            MetaOAuthState.expires_at > datetime.utcnow(),
        )
    )
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    oauth_state.is_used = True
    await db.commit()

    # 2️⃣ Store OAuth token
    await MetaOAuthService.store_token(
        db=db,
        user_id=oauth_state.user_id,
        code=code,
    )

    # 3️⃣ AUTO-SYNC AD ACCOUNTS
    await MetaAdAccountService.sync_user_ad_accounts(
        db=db,
        user_id=oauth_state.user_id,
    )

    # 4️⃣ AUTO-SYNC CAMPAIGNS
    await MetaCampaignService.sync_campaigns_for_user(
        db=db,
        user_id=oauth_state.user_id,
    )

    # 5️⃣ REDIRECT TO FRONTEND CAMPAIGNS PAGE
    return RedirectResponse(
        url="/campaigns",
        status_code=302,
    )


# ---------------------------------------------------------
# MANUAL SYNC — AD ACCOUNTS (DEV SAFE)
# ---------------------------------------------------------
@router.post("/adaccounts/sync")
async def sync_meta_ad_accounts(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)

    if not current_user:
        raise HTTPException(
            status_code=400,
            detail="No user available in development mode",
        )

    count = await MetaAdAccountService.sync_user_ad_accounts(
        db=db,
        user_id=current_user.id,
    )

    return {
        "status": "success",
        "ad_accounts_processed": count,
    }


# ---------------------------------------------------------
# MANUAL SYNC — CAMPAIGNS (DEV SAFE)
# ---------------------------------------------------------
@router.post("/campaigns/sync")
async def sync_meta_campaigns(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)

    if not current_user:
        raise HTTPException(
            status_code=400,
            detail="No user available in development mode",
        )

    count = await MetaCampaignService.sync_campaigns_for_user(
        db=db,
        user_id=current_user.id,
    )

    return {
        "status": "success",
        "campaigns_synced": count,
    }
