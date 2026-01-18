from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign
from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics

router = APIRouter(
    prefix="/daily-metrics",
    tags=["Daily Metrics"],
)


@router.get("/campaign/{campaign_id}")
async def get_campaign_daily_metrics(
    campaign_id: UUID,
    window: str = Query(
        "30d",
        description="Aggregation window: 1d,3d,7d,14d,30d,90d,lifetime",
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    SAFE read-only endpoint:
    - Returns EMPTY rows if no data
    - NEVER raises (wrapped)
    """

    window = window.lower()

    # Resolve campaign ownership
    result = await db.execute(
        select(Campaign.id).where(
            Campaign.id == campaign_id,
            Campaign.owner_user_id == user.id,
        )
    )
    owned = result.scalar_one_or_none()
    if not owned:
        # SAFE: do not leak existence — return empty
        return {
            "campaign_id": str(campaign_id),
            "window": window,
            "rows": [],
        }

    try:
        result = await db.execute(
            select(CampaignDailyMetrics)
            .where(
                CampaignDailyMetrics.campaign_id == campaign_id,
                CampaignDailyMetrics.window_type == window,
            )
            .order_by(CampaignDailyMetrics.date.desc())
        )
        rows = result.scalars().all()

    except Exception:
        # SAFETY GUARANTEE: never 500
        rows = []

    data = [
        {
            "date": r.date.isoformat(),
            "impressions": int(r.impressions or 0),
            "clicks": int(r.clicks or 0),
            "spend": float(r.spend or 0),
            "revenue": float(r.revenue or 0),
            "conversions": int(r.conversions or 0),
            "ctr": float(r.ctr) if r.ctr is not None else None,
            "cpc": float(r.cpc) if r.cpc is not None else None,
            "cpa": float(r.cpa) if r.cpa is not None else None,
            "roas": float(r.roas) if r.roas is not None else None,
        }
        for r in rows
    ]

    return {
        "campaign_id": str(campaign_id),
        "window": window,
        "rows": data,
    }
