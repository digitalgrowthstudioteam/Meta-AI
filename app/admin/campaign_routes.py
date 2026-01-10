from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.db_session import get_db
from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/admin/campaigns", tags=["Admin Campaigns"])


@router.get("", dependencies=[Depends(require_admin)])
async def list_campaigns(
    ai_active: Optional[bool] = Query(None),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Base query with JOIN to access user_id through ad accounts
    stmt = (
        select(Campaign, MetaAdAccount.user_id)
        .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
    )

    if ai_active is not None:
        stmt = stmt.where(Campaign.ai_active == ai_active)

    if user_id:
        stmt = stmt.where(MetaAdAccount.user_id == user_id)

    result = await db.execute(
        stmt.order_by(Campaign.created_at.desc())
    )
    rows = result.all()

    return [
        {
            "id": str(c.id),
            "user_id": str(u),
            "name": c.name,
            "objective": c.objective,
            "status": c.status,
            "ai_active": c.ai_active,
            "ai_execution_locked": c.ai_execution_locked,
            "is_manual": c.is_manual,
            "created_at": c.created_at.isoformat(),
        }
        for c, u in rows
    ]
