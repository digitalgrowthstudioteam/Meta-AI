from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User

from app.meta_api.models import (
    MetaOAuthToken,
    UserMetaAdAccount,
)
from app.campaigns.models import Campaign


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Phase 1 dashboard summary (READ-ONLY)

    Returns:
    - Meta connection status
    - Number of linked ad accounts
    - Total campaigns (synced)
    - AI-active campaigns (0 for Phase 1)
    """

    # --------------------------------------------------
    # 1. Meta connection status
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(MetaOAuthToken)
        .where(
            MetaOAuthToken.user_id == current_user.id,
            MetaOAuthToken.is_active.is_(True),
        )
    )
    meta_connected = result.scalar() > 0

    # --------------------------------------------------
    # 2. Ad accounts count
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == current_user.id)
    )
    ad_accounts = result.scalar() or 0

    # --------------------------------------------------
    # 3. Campaign count (if table exists / empty safe)
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(Campaign)
        .where(Campaign.user_id == current_user.id)
    )
    campaigns = result.scalar() or 0

    # --------------------------------------------------
    # 4. AI-active campaigns (Phase 1 = 0)
    # --------------------------------------------------
    ai_active = 0

    return {
        "meta_connected": meta_connected,
        "ad_accounts": ad_accounts,
        "campaigns": campaigns,
        "ai_active": ai_active,
    }
