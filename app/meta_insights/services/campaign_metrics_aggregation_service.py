"""
Campaign Metrics Aggregation Service

Purpose:
- Convert raw daily metrics into AI-ready windowed aggregates
- Safe to re-run (idempotent)
- No background jobs
- No Meta calls
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


class CampaignMetricsAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_for_date(self, as_of_date: date) -> None:
        """
        Entry point.
        Aggregates all campaigns for all windows as of a given date.
        """
        campaign_ids = await self._get_campaign_ids()

        for campaign_id in campaign_ids:
            for window_type, days in WINDOW_DEFINITIONS.items():
                await self._aggregate_campaign_window(
                    campaign_id=campaign_id,
                    window_type=window_type,
                    as_of_date=as_of_date,
                    days=days,
                )

        await self.db.commit()

    async def _get_campaign_ids(self) -> List[str]:
        result = await self.db.execute(
            text("SELECT id FROM campaigns WHERE is_archived = false")
        )
        return [str(row[0]) for row in result.fetchall()]

    async def _aggregate_campaign_window(
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
                COUNT(*)                        AS days_covered,
                SUM(impressions)                AS impressions,
                SUM(clicks)                     AS clicks,
                SUM(spend)                      AS spend,
                SUM(conversions)                AS conversions,
                SUM(conversion_value)           AS revenue
            FROM campaign_daily_metrics
            WHERE campaign_id = :campaign_id
              AND {date_filter}
        """

        params = {
            "campaign_id": campaign_id,
            "as_of_date": as_of_date,
            "window_start": window_start,
        }

        result = await self.db.execute(text(query), params)
        row = result.fetchone()

        if not row or row.impressions is None:
            return

        impressions = int(row.impressions or 0)
        clicks = int(row.clicks or 0)
        spend = float(row.spend or 0)
        conversions = int(row.conversions or 0)
        revenue = float(row.revenue or 0)

        ctr = (clicks / impressions) if impressions else None
        cpl = (spend / conversions) if conversions else None
        cpa = (spend / conversions) if conversions else None
        roas = (revenue / spend) if spend else None

        is_complete = (
            days is None or row.days_covered >= days
        )

        await self._upsert_aggregate(
            campaign_id=campaign_id,
            window_type=window_type,
            window_start=window_start,
            window_end=as_of_date,
            as_of_date=as_of_date,
            impressions=impressions,
            clicks=clicks,
            spend=spend,
            conversions=conversions,
            revenue=revenue,
            ctr=ctr,
            cpl=cpl,
            cpa=cpa,
            roas=roas,
            days_covered=row.days_covered,
            is_complete=is_complete,
        )

    async def _upsert_aggregate(self, **data) -> None:
        await self.db.execute(
            text(
                """
                INSERT INTO campaign_metrics_aggregates (
                    id,
                    campaign_id,
                    window_type,
                    window_start_date,
                    window_end_date,
                    as_of_date,
                    impressions,
                    clicks,
                    spend,
                    conversions,
                    revenue,
                    ctr,
                    cpl,
                    cpa,
                    roas,
                    days_covered,
                    is_complete_window,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :campaign_id,
                    :window_type,
                    :window_start,
                    :window_end,
                    :as_of_date,
                    :impressions,
                    :clicks,
                    :spend,
                    :conversions,
                    :revenue,
                    :ctr,
                    :cpl,
                    :cpa,
                    :roas,
                    :days_covered,
                    :is_complete,
                    :now,
                    :now
                )
                ON CONFLICT (campaign_id, window_type)
                DO UPDATE SET
                    window_start_date = EXCLUDED.window_start_date,
                    window_end_date   = EXCLUDED.window_end_date,
                    as_of_date        = EXCLUDED.as_of_date,
                    impressions       = EXCLUDED.impressions,
                    clicks            = EXCLUDED.clicks,
                    spend             = EXCLUDED.spend,
                    conversions       = EXCLUDED.conversions,
                    revenue           = EXCLUDED.revenue,
                    ctr               = EXCLUDED.ctr,
                    cpl               = EXCLUDED.cpl,
                    cpa               = EXCLUDED.cpa,
                    roas              = EXCLUDED.roas,
                    days_covered      = EXCLUDED.days_covered,
                    is_complete_window= EXCLUDED.is_complete_window,
                    updated_at        = EXCLUDED.updated_at
                """
            ),
            {
                **data,
                "now": datetime.utcnow(),
            },
        )
