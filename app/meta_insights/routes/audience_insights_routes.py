"""
Audience Insights Routes — Phase 8 (READ-ONLY)

Purpose:
- Expose audience / breakdown insights to frontend
- Powered by campaign_breakdown_aggregates
- NO Meta calls
- NO writes
- MUST NEVER 500
"""

from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

router = APIRouter(
    prefix="/audience-insights",
    tags=["Audience Insights"],
)


# =====================================================
# AUDIENCE INSIGHTS (CAMPAIGN LEVEL)
# =====================================================
@router.get("/campaign/{campaign_id}")
async def get_campaign_audience_insights(
    campaign_id: UUID,
    window: str = Query(
        "14d",
        description="Aggregation window: 1d,3d,7d,14d,30d,90d,lifetime",
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> Dict[str, Any]:
    """
    SAFE read-only endpoint.
    Returns EMPTY rows if no data exists.
    NEVER raises.
    """

    window = window.lower()

    query = """
        SELECT
            creative_id,
            placement,
            platform,
            region,
            gender,
            age_group,
            impressions,
            clicks,
            spend,
            conversions,
            revenue,
            ctr,
            cpl,
            cpa,
            roas
        FROM campaign_breakdown_aggregates
        WHERE campaign_id = :campaign_id
          AND window_type = :window
        ORDER BY impressions DESC
        LIMIT 200
    """

    try:
        result = await db.execute(
            text(query),
            {
                "campaign_id": str(campaign_id),
                "window": window,
            },
        )
        rows = result.fetchall()

    except Exception:
        # 🔒 ABSOLUTE SA
