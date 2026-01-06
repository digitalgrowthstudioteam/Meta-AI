import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db_session import get_db
from app.users.models import User
from app.auth.dependencies import get_current_user

from app.meta_api.oauth import build_meta_oauth_url
from app.meta_api.service import (
    MetaOAuthService,
    MetaAdAccountService,
    MetaCampaignService,
)
from app.meta_api.schemas import MetaConnectResponse
from app.meta_api.models import MetaOAuthState, MetaAdAccount, UserMetaAdAccount

router = APIRouter(prefix="/meta", tags=["Meta"])


# ---------------------------------------------------------
# CONNECT META (OAUTH)
# ---------------------------------------------------------
@router.get("/connect", response_model=MetaConnectResponse)
async def connect_meta_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state = str(uuid.uuid4())
    db.add(MetaOAuthState(user_id=current_user.id, state=state))
    await db.commit()

    return {"redirect_url": build_meta_oauth_url(state)}


# ---------------------------------------------------------
# OAUTH CALLBACK
# ---------------------------------------------------------
@router.get("/oauth/callback")
async def meta_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MetaOAuthState).where(
            MetaOAuthState.state == state,
            MetaOAuthState.is_used.is_(False),
            MetaOAuthState.expires_at > datetime.utcnow(),
        )
    )
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    oauth_state.is_used = True
    await db.commit()

    await MetaOAuthService.store_token(
        db=db,
        user_id=oauth_state.user_id,
        code=code,
    )

    await MetaAdAccountService.sync_user_ad_accounts(
        db=db,
        user_id=oauth_state.user_id,
    )

    return RedirectResponse(url="/campaigns", status_code=302)


# =========================================================
# LIST META AD ACCOUNTS (UUID + SELECT STATE)
# =========================================================
@router.get("/adaccounts")
async def list_meta_ad_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            MetaAdAccount.id,
            MetaAdAccount.account_name,
            UserMetaAdAccount.is_selected,
        )
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(UserMetaAdAccount.user_id == current_user.id)
        .order_by(MetaAdAccount.account_name)
    )

    return [
        {
            "id": r.id,
            "name": r.account_name,
            "is_selected": r.is_selected,
        }
        for r in result.all()
    ]


# =========================================================
# SELECT ONE META AD ACCOUNT (STRICT — ONE AT A TIME)
# =========================================================
@router.post("/adaccounts/select")
async def select_meta_ad_account(
    ad_account_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # deselect all
    await db.execute(
        update(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == current_user.id)
        .values(is_selected=False)
    )

    # select exactly one
    result = await db.execute(
        update(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == current_user.id,
            UserMetaAdAccount.meta_ad_account_id == ad_account_id,
        )
        .values(is_selected=True)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ad account not found")

    await db.commit()

    # sync campaigns ONLY for selected account
    await MetaCampaignService.sync_campaigns_for_user(
        db=db,
        user_id=current_user.id,
    )

    return {"status": "selected", "ad_account_id": str(ad_account_id)}
