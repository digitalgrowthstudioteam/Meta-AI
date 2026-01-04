"""
Industry Benchmark Aggregation Service

PHASE 9.4 — STEP 2

Purpose:
- Compute category-level industry benchmarks
- Windowed (7d / 30d / 90d)
- Objective-aware (LEAD / SALES)
- Read-only aggregation
- NO AI decisions
- NO Meta calls
"""

from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.models.industry_benchmarks import IndustryBenchmark


WINDOWS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


class IndustryBenchmarkAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # ENTRY POINT
    # =========================================================
    async def aggregate_for_date(self, as_of_date: date) -> None:
        """
        Computes benchmarks for all categories & objectives.
        Safe to run daily.
        """

        categories = await self._get_categories()

        for category in categories:
            for objective in ["LEAD", "SALES"]:
                for window_type, days in WINDOWS.items():
                    await self._aggregate_category_window(
                        category=category,
                        objective=objective,
                        window_type=window_type,
                        days=days,
                        as_of_date=as_of_date,
                    )

        await self.db.commit()

    # =========================================================
    # FETCH DISTINCT CATEGORIES
    # =========================================================
    async def _get_categories(self) -> List[str]:
        result = await self.db.execute(
            text(
                """
                SELECT DISTINCT category
                FROM campaign_category_map
                WHERE category IS NOT NULL
                """
            )
        )
        return [row[0] for row in result.fetchall()]

    # =========================================================
    # AGGREGATE SINGLE CATEGORY + WINDOW
    # =========================================================
    async def _aggregate_category_window(
        self,
        *,
        category: str,
        objective: str,
        window_type: str,
        days: int,
        as_of_date: date,
    ) -> None:

        window_start = as_of_date - timedelta(days=days - 1)

        result = await self.db.execute(
            text(
                """
                SELECT
                    COUNT(*)                                AS campaign_count,
                    AVG(ctr)                                AS avg_ctr,
                    AVG(cpl)                                AS avg_cpl,
                    AVG(cpa)                                AS avg_cpa,
                    AVG(roas)                               AS avg_roas,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY roas) AS p25_roas,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY roas) AS p50_roas,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY roas) AS p75_roas
                FROM campaign_metrics_aggregates cma
                JOIN campaign_category_map ccm
                  ON cma.campaign_id = ccm.campaign_id
                WHERE ccm.category = :category
                  AND cma.objective_type = :objective
                  AND cma.window_type = :window_type
                  AND cma.window_end_date BETWEEN :start AND :end
                """
            ),
            {
                "category": category,
                "objective": objective,
                "window_type": window_type,
                "start": window_start,
                "end": as_of_date,
            },
        )

        row = result.fetchone()
        if not row or row.campaign_count == 0:
            return

        await self._upsert_benchmark(
            category=category,
            objective=objective,
            window_type=window_type,
            as_of_date=as_of_date,
            row=row,
        )

    # =========================================================
    # UPSERT BENCHMARK
    # =========================================================
    async def _upsert_benchmark(
        self,
        *,
        category: str,
        objective: str,
        window_type: str,
        as_of_date: date,
        row,
    ) -> None:

        await self.db.execute(
            text(
                """
                INSERT INTO industry_benchmarks (
                    id,
                    category,
                    objective_type,
                    window_type,
                    as_of_date,
                    avg_ctr,
                    avg_cpl,
                    avg_cpa,
                    avg_roas,
                    p25_roas,
                    p50_roas,
                    p75_roas,
                    campaign_count,
                    created_at
                )
                VALUES (
                    gen_random_uuid(),
                    :category,
                    :objective,
                    :window_type,
                    :as_of_date,
                    :avg_ctr,
                    :avg_cpl,
                    :avg_cpa,
                    :avg_roas,
                    :p25_roas,
                    :p50_roas,
                    :p75_roas,
                    :campaign_count,
                    :now
                )
                ON CONFLICT (
                    category,
                    objective_type,
                    window_type,
                    as_of_date
                )
                DO UPDATE SET
                    avg_ctr = EXCLUDED.avg_ctr,
                    avg_cpl = EXCLUDED.avg_cpl,
                    avg_cpa = EXCLUDED.avg_cpa,
                    avg_roas = EXCLUDED.avg_roas,
                    p25_roas = EXCLUDED.p25_roas,
                    p50_roas = EXCLUDED.p50_roas,
                    p75_roas = EXCLUDED.p75_roas,
                    campaign_count = EXCLUDED.campaign_count
                """
            ),
            {
                "category": category,
                "objective": objective,
                "window_type": window_type,
                "as_of_date": as_of_date,
                "avg_ctr": row.avg_ctr,
                "avg_cpl": row.avg_cpl,
                "avg_cpa": row.avg_cpa,
                "avg_roas": row.avg_roas,
                "p25_roas": row.p25_roas,
                "p50_roas": row.p50_roas,
                "p75_roas": row.p75_roas,
                "campaign_count": row.campaign_count,
                "now": datetime.utcnow(),
            },
        )
