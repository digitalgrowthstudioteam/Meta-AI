"""
Campaign Daily Metrics Sync Service

PHASE 6.5 — META INSIGHTS INGESTION (LOCKED)

Purpose:
- Fetch daily Meta Insights per campaign
- Idempotent upsert into campaign_daily_metrics
- READ-ONLY Meta
- NO AI / NO inference
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
    # ENTRY POINT — DAILY SYNC (ADMIN ONLY)
    # =====================================================
    async def sync_for_date(self, target_date: date) -> Dict[str, int]:
        """
        Phase 6.5 responsibility:
        - Raw metrics ingestion
        - Stub-safe behavior (no false failures)
        """

        campaigns = await self._get_active_campaigns()

        synced = 0
        skipped = 0
        failed = 0

        for campaign in campaigns:
            try:
                insights = await self.client.fetch_daily_insights(
                    campaign=campaign,
                    target_date=target_date,
                )

                # -----------------------------
                # STUB / NO-DATA → SKIP
                # -----------------------------
                if not insights:
                    skipped += 1
                    continue

                impressions = int(insights.get("impressions", 0))
                clicks = int(insights.get("clicks", 0))
                spend = float(insights.get("spend", 0))
                leads = int(insights.get("leads", 0))
                purchases = int(insights.get("purchases", 0))
                revenue = float(insights.get("purchase_value", 0))

                # All-zero payload = Meta stub → SKIP (NOT failure)
                if (
                    impressions == 0
                    and clicks == 0
                    and spend == 0
                    and leads == 0
                    and purchases == 0
                    and revenue == 0
                ):
                    skipped += 1
                    continue

                row = self._normalize_campaign_metrics(
                    campaign=campaign,
                    insights=insights,
                    target_date=target_date,
                )

                await self._upsert_campaign_daily(row)
                synced += 1

            except Exception:
                failed += 1
                continue

        await self.db.commit()

        return {
            "synced_campaigns": synced,
            "skipped_campaigns": skipped,
            "failed_campaigns": failed,
        }

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
    # NORMALIZATION — CAMPAIGN LEVEL
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
    # UPSERT — CAMPAIGN DAILY METRICS (IDEMPOTENT)
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
