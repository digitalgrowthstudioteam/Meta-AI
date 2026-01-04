"""
Campaign Daily Metrics Sync Service

Purpose:
- Fetch daily Meta Insights per campaign
- Upsert into campaign_daily_metrics
- No duplication (campaign_id + date)
- Objective-aware (LEAD vs SALES)
- Safe, idempotent, async
"""

from datetime import date, datetime
from typing import Iterable, Dict, Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign
from app.meta_insights.clients.meta_campaign_insights_client import (
    MetaCampaignInsightsClient,
)


class CampaignDailyMetricsSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = MetaCampaignInsightsClient(db)

    async def sync_for_date(self, target_date: date) -> None:
        """
        Sync metrics for all active campaigns for a single date.
        Safe to re-run.
        """
        campaigns = await self._get_active_campaigns()

        for campaign in campaigns:
            insights = await self.client.fetch_daily_insights(
                campaign=campaign,
                target_date=target_date,
            )

            if not insights:
                continue

            row = self._normalize_metrics(campaign, insights, target_date)
            await self._upsert(row)

        await self.db.commit()

    async def _get_active_campaigns(self) -> Iterable[Campaign]:
        result = await self.db.execute(
            text(
                """
                SELECT *
                FROM campaigns
                WHERE is_deleted = false
                """
            )
        )
        return result.scalars().all()

    def _normalize_metrics(
        self,
        campaign: Campaign,
        insights: Dict[str, Any],
        target_date: date,
    ) -> Dict[str, Any]:
        impressions = int(insights.get("impressions", 0))
        clicks = int(insights.get("clicks", 0))
        spend = float(insights.get("spend", 0))

        leads = int(insights.get("leads", 0))
        purchases = int(insights.get("purchases", 0))
        revenue = float(insights.get("purchase_value", 0))

        ctr = (clicks / impressions) if impressions else None

        cpl = None
        cpa = None
        roas = None

        if campaign.objective == "LEAD" and leads > 0:
            cpl = spend / leads

        if campaign.objective == "SALES" and purchases > 0:
            cpa = spend / purchases
            roas = revenue / spend if spend > 0 else None

        return {
            "id": str(uuid4()),
            "campaign_id": str(campaign.id),
            "date": target_date,
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
            "updated_at": datetime.utcnow(),
        }

    async def _upsert(self, row: Dict[str, Any]) -> None:
        await self.db.execute(
            text(
                """
                INSERT INTO campaign_daily_metrics (
                    id,
                    campaign_id,
                    date,
                    impressions,
                    clicks,
                    spend,
                    leads,
                    purchases,
                    revenue,
                    ctr,
                    cpl,
                    cpa,
                    roas,
                    updated_at
                )
                VALUES (
                    :id,
                    :campaign_id,
                    :date,
                    :impressions,
                    :clicks,
                    :spend,
                    :leads,
                    :purchases,
                    :revenue,
                    :ctr,
                    :cpl,
                    :cpa,
                    :roas,
                    :updated_at
                )
                ON CONFLICT (campaign_id, date)
                DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    spend = EXCLUDED.spend,
                    leads = EXCLUDED.leads,
                    purchases = EXCLUDED.purchases,
                    revenue = EXCLUDED.revenue,
                    ctr = EXCLUDED.ctr,
                    cpl = EXCLUDED.cpl,
                    cpa = EXCLUDED.cpa,
                    roas = EXCLUDED.roas,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            row,
        )
