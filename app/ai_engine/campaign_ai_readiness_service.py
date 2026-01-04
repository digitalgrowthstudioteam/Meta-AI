"""
Campaign AI Readiness Service

PHASE 9.5 — BENCHMARK CALIBRATED (LOCKED)

Purpose:
- Prepare AI-consumable intelligence
- Score campaigns and breakdowns
- Compare time windows
- Detect fatigue, scale, decay
- Attach industry benchmark context
- Compute deltas vs industry for rule calibration
- NO ML (rules + math only)
"""

from typing import Dict, List, Literal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


WindowType = Literal["1d", "3d", "7d", "14d", "30d", "90d", "lifetime"]

# Phase 9.3 aligned breakdown dimensions
BreakdownDimension = Literal[
    "creative_id",
    "placement",
    "region",
    "age_group",
    "gender",
    "platform",
]


class CampaignAIReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CAMPAIGN-LEVEL AI SCORE (PHASE 9.5)
    # =========================================================
    async def get_campaign_ai_score(
        self,
        campaign_id: str,
        short_window: WindowType = "7d",
        long_window: WindowType = "30d",
    ) -> Dict:
        short = await self._get_campaign_window(campaign_id, short_window)
        long = await self._get_campaign_window(campaign_id, long_window)

        if not short or not long:
            return {"status": "insufficient_data"}

        score = self._score_performance(short, long)
        signals = self._detect_signals(short, long)

        benchmark = await self._get_industry_benchmark(
            campaign_id=campaign_id,
            window=short_window,
        )

        benchmark_ctx = self._build_benchmark_context(
            campaign_window=short,
            benchmark=benchmark,
        )

        return {
            "campaign_id": campaign_id,
            "short_window": short,
            "long_window": long,
            "ai_score": score,
            "signals": signals,
            "industry_benchmark": benchmark_ctx,
        }

    # =========================================================
    # BREAKDOWN RANKING (PHASE 9.3)
    # =========================================================
    async def rank_breakdowns(
        self,
        campaign_id: str,
        window: WindowType,
        dimension: BreakdownDimension,
        limit: int = 5,
    ) -> List[Dict]:
        result = await self.db.execute(
            text(
                f"""
                SELECT
                    {dimension} AS key,
                    impressions,
                    clicks,
                    spend,
                    conversions,
                    revenue,
                    ctr,
                    cpl,
                    cpa,
                    roas
                FROM campaign_breakdown_aggregates
                WHERE campaign_id = :campaign_id
                  AND window_type = :window
                  AND {dimension} IS NOT NULL
                ORDER BY
                    roas DESC NULLS LAST,
                    ctr DESC NULLS LAST,
                    conversions DESC
                LIMIT :limit
                """
            ),
            {
                "campaign_id": campaign_id,
                "window": window,
                "limit": limit,
            },
        )

        return [dict(row._mapping) for row in result.fetchall()]

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    async def _get_campaign_window(self, campaign_id: str, window: str) -> Dict | None:
        result = await self.db.execute(
            text(
                """
                SELECT *
                FROM campaign_metrics_aggregates
                WHERE campaign_id = :campaign_id
                  AND window_type = :window
                  AND is_complete_window = true
                """
            ),
            {"campaign_id": campaign_id, "window": window},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def _get_industry_benchmark(
        self,
        *,
        campaign_id: str,
        window: str,
    ) -> Dict | None:
        result = await self.db.execute(
            text(
                """
                SELECT
                    b.avg_ctr,
                    b.avg_cpl,
                    b.avg_cpa,
                    b.avg_roas,
                    b.p25_roas,
                    b.p50_roas,
                    b.p75_roas,
                    b.campaign_count
                FROM industry_benchmarks b
                WHERE b.category = (
                    SELECT category
                    FROM campaign_category_map
                    WHERE campaign_id = :campaign_id
                )
                  AND b.objective_type = (
                    SELECT objective
                    FROM campaigns
                    WHERE id = :campaign_id
                )
                  AND b.window_type = :window
                ORDER BY b.as_of_date DESC
                LIMIT 1
                """
            ),
            {
                "campaign_id": campaign_id,
                "window": window,
            },
        )

        row = result.fetchone()
        return dict(row._mapping) if row else None

    def _build_benchmark_context(
        self,
        *,
        campaign_window: Dict,
        benchmark: Dict | None,
    ) -> Dict | None:
        """
        Compute deltas vs industry benchmark for rules.
        """
        if not benchmark:
            return None

        ctx: Dict = {"metrics": {}}

        for metric in ("ctr", "cpl", "cpa", "roas"):
            campaign_value = campaign_window.get(metric)
            benchmark_value = benchmark.get(f"avg_{metric}")

            if campaign_value is None or benchmark_value is None:
                continue

            delta_pct = (
                ((campaign_value - benchmark_value) / benchmark_value) * 100
                if benchmark_value
                else None
            )

            ctx["metrics"][metric] = {
                "campaign": campaign_value,
                "benchmark": benchmark_value,
                "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
            }

        ctx["distribution"] = {
            "p25_roas": benchmark.get("p25_roas"),
            "p50_roas": benchmark.get("p50_roas"),
            "p75_roas": benchmark.get("p75_roas"),
        }
        ctx["campaign_count"] = benchmark.get("campaign_count")

        return ctx

    def _score_performance(self, short: Dict, long: Dict) -> float:
        score = 0.0

        if short.get("roas") and long.get("roas"):
            score += min((short["roas"] / long["roas"]) * 40, 40)

        if short.get("ctr") and long.get("ctr"):
            score += min((short["ctr"] / long["ctr"]) * 30, 30)

        if short.get("conversions") and long.get("conversions"):
            score += min(
                (short["conversions"] / long["conversions"]) * 30, 30
            )

        return round(score, 2)

    def _detect_signals(self, short: Dict, long: Dict) -> Dict:
        signals = {}

        if short.get("ctr") and long.get("ctr"):
            if short["ctr"] < long["ctr"] * 0.8:
                signals["fatigue"] = True
            elif short["ctr"] > long["ctr"] * 1.2:
                signals["scale"] = True

        if short.get("roas") and long.get("roas"):
            if short["roas"] < long["roas"] * 0.75:
                signals["decay"] = True

        return signals
