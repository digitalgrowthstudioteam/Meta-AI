from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.meta_api.models import UserMetaAdAccount
from app.campaigns.models import Campaign


router = APIRouter(prefix="/reports", tags=["Reports"])


# ---------------------------------------------------------
# REPORTS OVERVIEW — USER + SELECTED AD ACCOUNT ONLY
# ---------------------------------------------------------
@router.get("/overview")
async def reports_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_account = (
        await db.execute(
            select(UserMetaAdAccount)
            .where(
                UserMetaAdAccount.user_id == current_user.id,
                UserMetaAdAccount.is_selected.is_(True),
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if not selected_account:
        return {
            "status": "ok",
            "data": {
                "total_campaigns": 0,
                "ai_active_campaigns": 0,
                "lead_campaigns": 0,
                "sales_campaigns": 0,
            },
        }

    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.ad_account_id == selected_account.meta_ad_account_id,
            Campaign.is_archived.is_(False),
        )
    )
    campaigns = result.scalars().all()

    return {
        "status": "ok",
        "data": {
            "total_campaigns": len(campaigns),
            "ai_active_campaigns": len(
                [c for c in campaigns if c.ai_active]
            ),
            "lead_campaigns": len(
                [c for c in campaigns if c.objective == "OUTCOME_LEADS"]
            ),
            "sales_campaigns": len(
                [c for c in campaigns if c.objective == "OUTCOME_SALES"]
            ),
        },
    }


# ---------------------------------------------------------
# CAMPAIGN REPORTS — STRICT ACCOUNT SCOPE
# ---------------------------------------------------------
@router.get("/campaigns")
async def reports_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_account = (
        await db.execute(
            select(UserMetaAdAccount)
            .where(
                UserMetaAdAccount.user_id == current_user.id,
                UserMetaAdAccount.is_selected.is_(True),
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if not selected_account:
        return {"status": "ok", "campaigns": []}

    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.ad_account_id == selected_account.meta_ad_account_id,
            Campaign.is_archived.is_(False),
        )
    )

    return {
        "status": "ok",
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "objective": c.objective,
                "ai_active": c.ai_active,
            }
            for c in result.scalars().all()
        ],
    }


# ---------------------------------------------------------
# PERFORMANCE REPORTS — LOCKED (PHASE SAFE)
# ---------------------------------------------------------
@router.get("/performance")
async def reports_performance(
    current_user: User = Depends(get_current_user),
):
    return {
        "status": "ok",
        "metrics": {
            "ctr": None,
            "cpl": None,
            "cpa": None,
            "roas": None,
        },
    }
