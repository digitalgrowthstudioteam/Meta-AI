"""
Campaign Metrics Aggregation Service

Purpose:
- Convert raw daily metrics into AI-ready windowed aggregates
- Derive fatigue + expansion signals for Audience Intelligence
- Safe to re-run (idempotent)
- No background jobs
- No Meta calls
"""

from datetime import date, timedelta, datetime
from typing import List, Optional

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

    # =====================================================
    # ENTRY POINT
    # =====================================================
    async def aggregate_for_date(self, as_of_date: date) -> None:
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

    # =====================================================
    # WINDOW AGGREGATION
    # =====================================================
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
                COUNT(*)              AS days_covered,
                SUM(impressions)      AS impressions,
                SUM(clicks)           AS clicks,
                SUM(spend)            AS spend,
                SUM(conversions)      AS conversions,
                SUM(conversion_value) AS revenue
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
        cpa = (spend / conversions) if conversions else None
        roas = (revenue / spend) if spend else None

        is_complete = days is None or row.days_covered >= days

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
            cpa=cpa,
            roas=roas,
            days_covered=row.days_covered,
            is_complete=is_complete,
        )

    # =====================================================
    # FATIGUE + EXPANSION SIGNALS (PHASE 20)
    # =====================================================
    async def compute_audience_signals(
        self,
        *,
        campaign_id: str,
        short_window: str = "7d",
        long_window: str = "30d",
    ) -> dict:
        """
        Derives fatigue & expansion signals from aggregates.
        Read-only. No DB writes.
        """

        def _get(window: str):
            result = self.db.execute(
                text(
                    """
                    SELECT impressions, ctr, cpa, roas
                    FROM campaign_metrics_aggregates
                    WHERE campaign_id = :cid AND window_type = :wt
                    """
                ),
                {"cid": campaign_id, "wt": window},
            )
            return result

        short = await (await _get(short_window)).fetchone()
        long = await (await _get(long_window)).fetchone()

        if not short or not long:
            return {}

        # -------------------------
        # FATIGUE
        # -------------------------
        ctr_trend = (
            (short.ctr - long.ctr) / long.ctr
            if short.ctr and long.ctr
            else None
        )

        fatigue_score = 0.0
        if ctr_trend is not None and ctr_trend < -0.15:
            fatigue_score = min(abs(ctr_trend), 1.0)

        # -------------------------
        # EXPANSION
        # -------------------------
        conversion_lift = (
            (short.roas - long.roas) / long.roas
            if short.roas and long.roas
            else None
        )

        return {
            "fatigue_score": fatigue_score,
            "ctr_trend": ctr_trend,
            "conversion_lift": conversion_lift,
        }

    # =====================================================
    # UPSERT
    # =====================================================
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
                    :cpa,
                    :roas,
                    :days_covered,
                    :is_complete,
                    :now,
                    :now
                )
                ON CONFLICT (campaign_id, window_type)
                DO UPDATE SET
                    window_start_date   = EXCLUDED.window_start_date,
                    window_end_date     = EXCLUDED.window_end_date,
                    as_of_date          = EXCLUDED.as_of_date,
                    impressions         = EXCLUDED.impressions,
                    clicks              = EXCLUDED.clicks,
                    spend               = EXCLUDED.spend,
                    conversions         = EXCLUDED.conversions,
                    revenue             = EXCLUDED.revenue,
                    ctr                 = EXCLUDED.ctr,
                    cpa                 = EXCLUDED.cpa,
                    roas                = EXCLUDED.roas,
                    days_covered        = EXCLUDED.days_covered,
                    is_complete_window  = EXCLUDED.is_complete_window,
                    updated_at          = EXCLUDED.updated_at
                """
            ),
            {
                **data,
                "now": datetime.utcnow(),
            },
        )
