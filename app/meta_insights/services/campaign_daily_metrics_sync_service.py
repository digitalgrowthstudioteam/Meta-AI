"""
Campaign Daily Metrics Sync Service

PHASE 9.3 — AGGREGATION READY (FOUNDATION)

Purpose:
- Fetch daily Meta Insights per campaign
- Upsert into campaign_daily_metrics
- NO inference
- NO AI
- NO mutation of Meta
- Prepare clean, normalized data for downstream aggregations
"""

from datetime import date, datetime
from typing import Dict, Any
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

    # =====================================================
    # ENTRY POINT — DAILY SYNC (LOCKED)
    # =====================================================
    async def sync_for_date(self, target_date: date) -> None:
        """
        Phase 6.x responsibility:
        - Raw, immutable metrics ingestion
        - Campaign-level only
        """

        campaigns = await self._get_active_campaigns()

        for campaign in campaigns:
            insights = await self.client.fetch_daily_insights(
                campaign=campaign,
                target_date=target_date,
            )

            if not insights:
                continue

            row = self._normalize_campaign_metrics(
                campaign=campaign,
                insights=insights,
                target_date=target_date,
            )

            await self._upsert_campaign_daily(row)

        await self.db.commit()

    # =====================================================
    # FETCH CAMPAIGNS (READ-ONLY)
    # =====================================================
    async def _get_active_campaigns(self):
        result = await self.db.execute(
            text(
                """
                SELECT *
                FROM campaigns
                WHERE is_archived = FALSE
                """
            )
        )
        return result.scalars().all()

    # =====================================================
    # NORMALIZATION — CAMPAIGN LEVEL (LOCKED)
    # =====================================================
    def _normalize_campaign_metrics(
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

    # =====================================================
    # UPSERT — CAMPAIGN DAILY METRICS (LOCKED)
    # =====================================================
    async def _upsert_campaign_daily(self, row: Dict[str, Any]) -> None:
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
