"""
Industry Benchmark Aggregation Service

PHASE 9.4 — STEP 2 (COMPUTATION)

Purpose:
- Compute industry/category benchmarks from campaign aggregates
- Populate industry_benchmarks table
- Read-only analytics (NO AI, NO Meta, NO decisions)
"""

from datetime import date, datetime
from typing import List, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.models.industry_benchmarks import IndustryBenchmark


WINDOWS = ["7d", "30d", "90d"]


class IndustryBenchmarkAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================
    # ENTRY POINT
    # =====================================================
    async def compute_for_date(self, as_of_date: date) -> int:
        """
        Compute benchmarks for all categories/objectives/windows.
        Idempotent per (category, objective, window, date).
        """
        rows_inserted = 0

        for window in WINDOWS:
            rows = await self._fetch_aggregates(window, as_of_date)

            for row in rows:
                await self._upsert_benchmark(
                    category=row["category"],
                    objective=row["objective_type"],
                    window=window,
                    as_of_date=as_of_date,
                    metrics=row,
                )
                rows_inserted += 1

        await self.db.commit()
        return rows_inserted

    # =====================================================
    # FETCH SOURCE DATA
    # =====================================================
    async def _fetch_aggregates(
        self,
        window: str,
        as_of_date: date,
    ) -> List[Dict]:
        """
        Pull aggregated campaign metrics grouped by
        category + objective for a given window.
        """
        result = await self.db.execute(
            text(
                """
                SELECT
                    ccm.category                         AS category,
                    c.objective                          AS objective_type,
                    COUNT(*)                             AS campaign_count,
                    AVG(a.ctr)                           AS avg_ctr,
                    AVG(a.cpl)                           AS avg_cpl,
                    AVG(a.cpa)                           AS avg_cpa,
                    AVG(a.roas)                          AS avg_roas,
                    PERCENTILE_CONT(0.25)
                        WITHIN GROUP (ORDER BY a.roas)   AS p25_roas,
                    PERCENTILE_CONT(0.50)
                        WITHIN GROUP (ORDER BY a.roas)   AS p50_roas,
                    PERCENTILE_CONT(0.75)
                        WITHIN GROUP (ORDER BY a.roas)   AS p75_roas
                FROM campaign_metrics_aggregates a
                JOIN campaigns c
                    ON c.id = a.campaign_id
                JOIN campaign_category_map ccm
                    ON ccm.campaign_id = c.id
                WHERE a.window_type = :window
                  AND a.is_complete_window = TRUE
                  AND a.window_end_date = :as_of_date
                GROUP BY ccm.category, c.objective
                """
            ),
            {
                "window": window,
                "as_of_date": as_of_date,
            },
        )

        return [dict(row._mapping) for row in result.fetchall()]

    # =====================================================
    # UPSERT BENCHMARK
    # =====================================================
    async def _upsert_benchmark(
        self,
        *,
        category: str,
        objective: str,
        window: str,
        as_of_date: date,
        metrics: Dict,
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
                    :objective_type,
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
                "objective_type": objective,
                "window_type": window,
                "as_of_date": as_of_date,
                "avg_ctr": metrics.get("avg_ctr"),
                "avg_cpl": metrics.get("avg_cpl"),
                "avg_cpa": metrics.get("avg_cpa"),
                "avg_roas": metrics.get("avg_roas"),
                "p25_roas": metrics.get("p25_roas"),
                "p50_roas": metrics.get("p50_roas"),
                "p75_roas": metrics.get("p75_roas"),
                "campaign_count": metrics.get("campaign_count", 0),
                "now": datetime.utcnow(),
            },
        )
