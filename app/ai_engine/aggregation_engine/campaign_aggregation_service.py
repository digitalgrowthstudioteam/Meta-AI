from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta, datetime
from typing import Dict, List

from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics
from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction


class CampaignAggregationService:
    """
    Materializes aggregated campaign performance over
    fixed time windows for AI consumption.

    Responsibilities:
    - Aggregate raw daily metrics
    - Produce windowed summaries (1D, 3D, 7D, 14D, 30D, 90D, LIFETIME)
    - Provide deterministic inputs for AI decisions
    - Support explainability & confidence scoring

    This service does NOT:
    - Make decisions
    - Suggest actions
    - Talk to Meta
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
        Builds aggregated metrics for a single campaign
        across all supported time windows.

        Returns:
        {
            "1D": {...},
            "3D": {...},
            ...
        }
        """

        aggregates: Dict[str, Dict] = {}

        for window, days in CampaignAggregationService.TIME_WINDOWS.items():
            stmt = select(
                func.sum(CampaignDailyMetrics.impressions).label("impressions"),
                func.sum(CampaignDailyMetrics.clicks).label("clicks"),
                func.sum(CampaignDailyMetrics.spend).label("spend"),
                func.sum(CampaignDailyMetrics.conversions).label("conversions"),
                func.sum(CampaignDailyMetrics.conversion_value).label("conversion_value"),
            ).where(
                CampaignDailyMetrics.campaign_id == campaign.id,
                CampaignDailyMetrics.metric_date <= as_of_date,
            )

            if days is not None:
                start_date = as_of_date - timedelta(days=days - 1)
                stmt = stmt.where(
                    CampaignDailyMetrics.metric_date >= start_date
                )

            result = await db.execute(stmt)
            row = result.one()

            impressions = int(row.impressions or 0)
            clicks = int(row.clicks or 0)
            spend = float(row.spend or 0.0)
            conversions = int(row.conversions or 0)
            conversion_value = float(row.conversion_value or 0.0)

            # Derived metrics (safe math)
            ctr = (clicks / impressions * 100) if impressions > 0 else None
            cpl = (spend / conversions) if conversions > 0 else None
            cpa = (spend / conversions) if conversions > 0 else None
            roas = (conversion_value / spend) if spend > 0 else None

            aggregates[window] = {
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "conversions": conversions,
                "conversion_value": conversion_value,
                "ctr": ctr,
                "cpl": cpl,
                "cpa": cpa,
                "roas": roas,
                "as_of_date": as_of_date,
                "objective_type": campaign.objective,
                "window": window,
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

        Returns:
        {
            campaign_id: {
                "1D": {...},
                "3D": {...},
                ...
            }
        }
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
