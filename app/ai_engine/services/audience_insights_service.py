"""
Audience Insights Service

PHASE 8 — READ-ONLY AI AUDIENCE INSIGHTS

Purpose:
- Analyze breakdown metrics
- Detect outperforming / underperforming segments
- Generate SAFE suggestions
- NO Meta mutation
- NO DB writes
"""

from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.meta_insights.models.campaign_breakdown_daily_metrics import (
    CampaignBreakdownDailyMetrics,
)


class AudienceInsightsService:
    """
    Produces explainable audience insights for AI layer.
    """

    # --------------------------------------------------
    # PUBLIC ENTRY
    # --------------------------------------------------
    @staticmethod
    async def generate_insights(
        *,
        db: AsyncSession,
        campaign_id: UUID,
        lookback_days: int = 14,
    ) -> List[Dict[str, Any]]:
        """
        Returns ranked audience insights.

        Output is READ-ONLY suggestions:
        - keep
        - expand
        - reduce
        """

        stmt = (
            select(
                CampaignBreakdownDailyMetrics.age_group,
                CampaignBreakdownDailyMetrics.gender,
                CampaignBreakdownDailyMetrics.platform,
                CampaignBreakdownDailyMetrics.placement,
                func.sum(CampaignBreakdownDailyMetrics.spend).label("spend"),
                func.sum(CampaignBreakdownDailyMetrics.conversions).label("conversions"),
                func.sum(CampaignBreakdownDailyMetrics.conversion_value).label("revenue"),
            )
            .where(
                CampaignBreakdownDailyMetrics.campaign_id == campaign_id,
            )
            .group_by(
                CampaignBreakdownDailyMetrics.age_group,
                CampaignBreakdownDailyMetrics.gender,
                CampaignBreakdownDailyMetrics.platform,
                CampaignBreakdownDailyMetrics.placement,
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        insights: List[Dict[str, Any]] = []

        for row in rows:
            spend = float(row.spend or 0)
            conversions = int(row.conversions or 0)
            revenue = float(row.revenue or 0)

            if spend == 0:
                continue

            cpa = (spend / conversions) if conversions else None
            roas = (revenue / spend) if spend else None

            recommendation = "keep"
            reason = "Stable performance"

            if roas and roas >= 2:
                recommendation = "expand"
                reason = "High ROAS audience segment"
            elif cpa and cpa > spend * 0.8:
                recommendation = "reduce"
                reason = "High cost, low return segment"

            insights.append(
                {
                    "age_group": row.age_group,
                    "gender": row.gender,
                    "platform": row.platform,
                    "placement": row.placement,
                    "spend": spend,
                    "conversions": conversions,
                    "revenue": revenue,
                    "cpa": cpa,
                    "roas": roas,
                    "recommendation": recommendation,
                    "reason": reason,
                }
            )

        return insights
