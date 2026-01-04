from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import Dict, List

from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics
from app.campaigns.models import Campaign


class CampaignAggregationService:
    """
    PHASE 6.5+ — MATERIALIZED AGGREGATIONS

    Aggregates RAW campaign_daily_metrics into
    deterministic time-window summaries for AI.
    """

    TIME_WINDOWS = {
        "1D": 1,
        "3D": 3,
        "7D": 7,
        "14D": 14,
        "30D": 30,
        "90D": 90,
        "LIFETIME": None,
    }

    @staticmethod
    async def aggregate_for_campaign(
        *,
        db: AsyncSession,
        campaign: Campaign,
        as_of_date: date,
    ) -> Dict[str, Dict]:
        """
        Aggregates metrics for ONE campaign across all windows.
        """

        aggregates: Dict[str, Dict] = {}

        for window, days in CampaignAggregationService.TIME_WINDOWS.items():
            stmt = select(
                func.sum(CampaignDailyMetrics.impressions).label("impressions"),
                func.sum(CampaignDailyMetrics.clicks).label("clicks"),
                func.sum(CampaignDailyMetrics.spend).label("spend"),
                func.sum(CampaignDailyMetrics.leads).label("leads"),
                func.sum(CampaignDailyMetrics.purchases).label("purchases"),
                func.sum(CampaignDailyMetrics.revenue).label("revenue"),
            ).where(
                CampaignDailyMetrics.campaign_id == campaign.id,
                CampaignDailyMetrics.date <= as_of_date,
            )

            if days is not None:
                start_date = as_of_date - timedelta(days=days - 1)
                stmt = stmt.where(CampaignDailyMetrics.date >= start_date)

            result = await db.execute(stmt)
            row = result.one()

            impressions = int(row.impressions or 0)
            clicks = int(row.clicks or 0)
            spend = float(row.spend or 0.0)
            leads = int(row.leads or 0)
            purchases = int(row.purchases or 0)
            revenue = float(row.revenue or 0.0)

            ctr = (clicks / impressions) if impressions > 0 else None
            cpl = (spend / leads) if leads > 0 else None
            cpa = (spend / purchases) if purchases > 0 else None
            roas = (revenue / spend) if spend > 0 else None

            aggregates[window] = {
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "leads": leads,
                "purchases": purchases,
                "revenue": revenue,
                "ctr": ctr,
                "cpl": cpl,
                "cpa": cpa,
                "roas": roas,
                "window": window,
                "as_of_date": as_of_date,
                "objective_type": campaign.objective,
            }

        return aggregates

    @staticmethod
    async def aggregate_for_all_ai_campaigns(
        *,
        db: AsyncSession,
        as_of_date: date,
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Aggregates metrics for ALL AI-active campaigns.
        """

        stmt = select(Campaign).where(
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
            Campaign.admin_locked.is_(False),
        )

        result = await db.execute(stmt)
        campaigns: List[Campaign] = result.scalars().all()

        all_results: Dict[str, Dict[str, Dict]] = {}

        for campaign in campaigns:
            aggregates = await CampaignAggregationService.aggregate_for_campaign(
                db=db,
                campaign=campaign,
                as_of_date=as_of_date,
            )
            all_results[str(campaign.id)] = aggregates

        return all_results
