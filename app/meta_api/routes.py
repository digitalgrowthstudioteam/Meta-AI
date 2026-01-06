import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db_session import get_db
from app.users.models import User

from app.meta_api.oauth import build_meta_oauth_url
from app.meta_api.service import (
    MetaOAuthService,
    MetaAdAccountService,
    MetaCampaignService,
)
from app.meta_api.schemas import MetaConnectResponse
from app.meta_api.models import MetaOAuthState, MetaAdAccount, UserMetaAdAccount

router = APIRouter(prefix="/meta", tags=["Meta"])


# =========================================================
# DEV MODE USER RESOLUTION (TEMPORARY)
# =========================================================
async def get_dev_user(db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none()


# ---------------------------------------------------------
# CONNECT META (OAUTH)
# ---------------------------------------------------------
@router.get("/connect", response_model=MetaConnectResponse)
async def connect_meta_account(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)
    if not current_user:
        raise HTTPException(status_code=400, detail="No user available")

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
# LIST ALL META AD ACCOUNTS (WITH SELECTION STATE)
# =========================================================
@router.get("/adaccounts")
async def list_meta_ad_accounts(
    db: AsyncSession = Depends(get_db),
):
    user = await get_dev_user(db)
    if not user:
        raise HTTPException(status_code=400, detail="No user available")

    result = await db.execute(
        select(
            MetaAdAccount.id,
            MetaAdAccount.meta_account_id,
            MetaAdAccount.account_name,
            UserMetaAdAccount.is_selected,
        )
        .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
        .where(UserMetaAdAccount.user_id == user.id)
        .order_by(MetaAdAccount.account_name)
    )

    return [
        {
            "id": r.id,
            "meta_account_id": r.meta_account_id,
            "account_name": r.account_name,
            "is_selected": r.is_selected,
        }
        for r in result.all()
    ]


# =========================================================
# SELECT ONE META AD ACCOUNT (ATOMIC)
# =========================================================
@router.post("/adaccounts/select")
async def select_meta_ad_account(
    meta_ad_account_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await get_dev_user(db)
    if not user:
        raise HTTPException(status_code=400, detail="No user available")

    # deselect all
    await db.execute(
        update(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == user.id)
        .values(is_selected=False)
    )

    # select one
    result = await db.execute(
        update(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.meta_ad_account_id
            == select(MetaAdAccount.id)
            .where(MetaAdAccount.meta_account_id == meta_ad_account_id)
            .scalar_subquery(),
        )
        .values(is_selected=True)
    )

    await db.commit()

    # sync campaigns ONLY for selected account
    await MetaCampaignService.sync_campaigns_for_user(
        db=db,
        user_id=user.id,
    )

    return {"status": "selected", "meta_ad_account_id": meta_ad_account_id}
