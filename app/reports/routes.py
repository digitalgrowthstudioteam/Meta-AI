from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import get_session_context
from app.campaigns.models import Campaign


router = APIRouter(prefix="/reports", tags=["Reports"])


# ---------------------------------------------------------
# REPORTS OVERVIEW — STRICT SESSION CONTEXT
# ---------------------------------------------------------
@router.get("/overview")
async def reports_overview(
    db: AsyncSession = Depends(get_db),
    session: dict = Depends(get_session_context),
):
    ad_account = session["ad_account"]

    if not ad_account:
        return {
            "status": "ok",
            "data": {
                "total_campaigns": 0,
                "ai_active_campaigns": 0,
                "lead_campaigns": 0,
                "sales_campaigns": 0,
            },
        }

    ad_account_id = UUID(ad_account["id"])

    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.ad_account_id == ad_account_id,
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
# CAMPAIGN REPORTS — STRICT SESSION CONTEXT
# ---------------------------------------------------------
@router.get("/campaigns")
async def reports_campaigns(
    db: AsyncSession = Depends(get_db),
    session: dict = Depends(get_session_context),
):
    ad_account = session["ad_account"]

    if not ad_account:
        return {"status": "ok", "campaigns": []}

    ad_account_id = UUID(ad_account["id"])

    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.ad_account_id == ad_account_id,
            Campaign.is_archived.is_(False),
        )
    )

    return {
        "status": "ok",
        "campaigns": [
            {
                "id": str(c.id),
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
    session: dict = Depends(get_session_context),
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
