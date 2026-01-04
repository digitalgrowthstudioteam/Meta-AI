"""
Campaign vs Industry Benchmark Service

PHASE 9.4 — STEP 3

Purpose:
- Compare a campaign's performance against industry benchmarks
- Category-aware
- Objective-aware (LEAD / SALES)
- Windowed (7d / 30d / 90d)
- Read-only intelligence layer
- NO decisions
- NO Meta calls
"""

from typing import Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CampaignVsBenchmarkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # PUBLIC ENTRY POINT
    # =========================================================
    async def compare(
        self,
        *,
        campaign_id: str,
        window_type: str,
    ) -> Dict:
        """
        Returns benchmark comparison context for a campaign.

        Example output:
        {
            "status": "ok",
            "relative_position": "above_average",
            "metrics": {
                "roas": { "campaign": 3.2, "industry_avg": 2.4, "delta_pct": 33.3 },
                "ctr":  { "campaign": 1.8, "industry_avg": 1.2, "delta_pct": 50.0 }
            }
        }
        """

        campaign_row = await self._get_campaign_metrics(
            campaign_id=campaign_id,
            window_type=window_type,
        )

        if not campaign_row:
            return {"status": "insufficient_data"}

        benchmark_row = await self._get_benchmark_metrics(
            campaign_id=campaign_id,
            window_type=window_type,
        )

        if not benchmark_row or benchmark_row.campaign_count < 3:
            return {"status": "benchmark_unavailable"}

        return self._build_comparison(campaign_row, benchmark_row)

    # =========================================================
    # FETCH CAMPAIGN METRICS
    # =========================================================
    async def _get_campaign_metrics(
        self,
        *,
        campaign_id: str,
        window_type: str,
    ) -> Optional[Dict]:
        result = await self.db.execute(
            text(
                """
                SELECT
                    cma.ctr,
                    cma.cpl,
                    cma.cpa,
                    cma.roas,
                    cma.objective_type,
                    ccm.category
                FROM campaign_metrics_aggregates cma
                JOIN campaign_category_map ccm
                  ON cma.campaign_id = ccm.campaign_id
                WHERE cma.campaign_id = :campaign_id
                  AND cma.window_type = :window_type
                  AND cma.is_complete_window = true
                """
            ),
            {
                "campaign_id": campaign_id,
                "window_type": window_type,
            },
        )

        row = result.fetchone()
        return dict(row._mapping) if row else None

    # =========================================================
    # FETCH INDUSTRY BENCHMARK
    # =========================================================
    async def _get_benchmark_metrics(
        self,
        *,
        campaign_id: str,
        window_type: str,
    ):
        result = await self.db.execute(
            text(
                """
                SELECT
                    ib.avg_ctr,
                    ib.avg_cpl,
                    ib.avg_cpa,
                    ib.avg_roas,
                    ib.p25_roas,
                    ib.p50_roas,
                    ib.p75_roas,
                    ib.campaign_count
                FROM industry_benchmarks ib
                JOIN campaign_category_map ccm
                  ON ib.category = ccm.category
                WHERE ccm.campaign_id = :campaign_id
                  AND ib.window_type = :window_type
                ORDER BY ib.as_of_date DESC
                LIMIT 1
                """
            ),
            {
                "campaign_id": campaign_id,
                "window_type": window_type,
            },
        )

        return result.fetchone()

    # =========================================================
    # BUILD COMPARISON CONTEXT
    # =========================================================
    def _build_comparison(self, campaign: Dict, benchmark) -> Dict:
        metrics = {}

        def compare_metric(name, campaign_val, benchmark_val):
            if campaign_val is None or benchmark_val is None:
                return None

            delta_pct = (
                ((campaign_val - benchmark_val) / benchmark_val) * 100
                if benchmark_val != 0
                else None
            )

            return {
                "campaign": round(float(campaign_val), 4),
                "industry_avg": round(float(benchmark_val), 4),
                "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
            }

        metrics["roas"] = compare_metric(
            "roas", campaign.get("roas"), benchmark.avg_roas
        )
        metrics["ctr"] = compare_metric(
            "ctr", campaign.get("ctr"), benchmark.avg_ctr
        )
        metrics["cpl"] = compare_metric(
            "cpl", campaign.get("cpl"), benchmark.avg_cpl
        )
        metrics["cpa"] = compare_metric(
            "cpa", campaign.get("cpa"), benchmark.avg_cpa
        )

        # Relative position (simple & explainable)
        relative_position = "average"
        if campaign.get("roas") and benchmark.p75_roas:
            if campaign["roas"] >= benchmark.p75_roas:
                relative_position = "top_quartile"
            elif campaign["roas"] < benchmark.p25_roas:
                relative_position = "bottom_quartile"

        return {
            "status": "ok",
            "relative_position": relative_position,
            "metrics": metrics,
        }
