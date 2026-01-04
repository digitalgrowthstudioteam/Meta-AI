"""
Campaign Breakdown Aggregation Service

PHASE 9.3.2 — CORRECTED & LOCKED

Purpose:
- Aggregate performance by creative, placement, geography, demographics, device
- Windowed (1D, 3D, 7D, 14D, 30D, 90D, Lifetime)
- Source of truth: campaign_breakdown_daily_metrics
"""

from datetime import date, timedelta, datetime
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


WINDOW_DEFINITIONS = {
    "1d": 1,
    "3d": 3,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "90d": 90,
    "lifetime": None,
}


class CampaignBreakdownAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================
    # PUBLIC ENTRY POINT
    # =====================================================
    async def aggregate_for_date(self, as_of_date: date) -> None:
        campaign_ids = await self._get_campaign_ids()

        for campaign_id in campaign_ids:
            for window_type, days in WINDOW_DEFINITIONS.items():
                await self._aggregate_campaign_breakdowns(
                    campaign_id=campaign_id,
                    window_type=window_type,
                    as_of_date=as_of_date,
                    days=days,
                )

        await self.db.commit()

    # =====================================================
    # FETCH ACTIVE CAMPAIGNS
    # =====================================================
    async def _get_campaign_ids(self) -> List[str]:
        result = await self.db.execute(
            text(
                """
                SELECT id
                FROM campaigns
                WHERE is_archived = FALSE
                """
            )
        )
        return [str(row[0]) for row in result.fetchall()]

    # =====================================================
    # CORE AGGREGATION LOGIC (FIXED)
    # =====================================================
    async def _aggregate_campaign_breakdowns(
        self,
        campaign_id: str,
        window_type: str,
        as_of_date: date,
        days: int | None,
    ) -> None:
        if days is None:
            date_filter = "metric_date <= :as_of_date"
            window_start = None
        else:
            window_start = as_of_date - timedelta(days=days - 1)
            date_filter = "metric_date BETWEEN :window_start AND :as_of_date"

        query = f"""
            SELECT
                creative_id,
                placement,
                region,
                gender,
                age_group,
                platform,
                SUM(impressions)      AS impressions,
                SUM(clicks)           AS clicks,
                SUM(spend)            AS spend,
                SUM(conversions)      AS conversions,
                SUM(conversion_value) AS revenue
            FROM campaign_breakdown_daily_metrics
            WHERE campaign_id = :campaign_id
              AND {date_filter}
            GROUP BY
                creative_id,
                placement,
                region,
                gender,
                age_group,
                platform
        """

        params = {
            "campaign_id": campaign_id,
            "as_of_date": as_of_date,
            "window_start": window_start,
        }

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        for row in rows:
            impressions = int(row.impressions or 0)
            clicks = int(row.clicks or 0)
            spend = float(row.spend or 0)
            conversions = int(row.conversions or 0)
            revenue = float(row.revenue or 0)

            ctr = (clicks / impressions) if impressions else None
            cpl = (spend / conversions) if conversions else None
            cpa = (spend / conversions) if conversions else None
            roas = (revenue / spend) if spend else None

            await self._upsert_breakdown(
                campaign_id=campaign_id,
                window_type=window_type,
                window_start=window_start,
                window_end=as_of_date,
                creative_id=row.creative_id,
                placement=row.placement,
                region=row.region,
                gender=row.gender,
                age_group=row.age_group,
                platform=row.platform,
                impressions=impressions,
                clicks=clicks,
                spend=spend,
                conversions=conversions,
                revenue=revenue,
                ctr=ctr,
                cpl=cpl,
                cpa=cpa,
                roas=roas,
            )

    # =====================================================
    # UPSERT AGGREGATES (IDEMPOTENT)
    # =====================================================
    async def _upsert_breakdown(self, **data) -> None:
        await self.db.execute(
            text(
                """
                INSERT INTO campaign_breakdown_aggregates (
                    id,
                    campaign_id,
                    window_type,
                    window_start_date,
                    window_end_date,
                    creative_id,
                    placement,
                    region,
                    gender,
                    age_group,
                    platform,
                    impressions,
                    clicks,
                    spend,
                    conversions,
                    revenue,
                    ctr,
                    cpl,
                    cpa,
                    roas,
                    created_at
                )
                VALUES (
                    gen_random_uuid(),
                    :campaign_id,
                    :window_type,
                    :window_start,
                    :window_end,
                    :creative_id,
                    :placement,
                    :region,
                    :gender,
                    :age_group,
                    :platform,
                    :impressions,
                    :clicks,
                    :spend,
                    :conversions,
                    :revenue,
                    :ctr,
                    :cpl,
                    :cpa,
                    :roas,
                    :now
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                **data,
                "now": datetime.utcnow(),
            },
        )
