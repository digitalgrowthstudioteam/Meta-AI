from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.campaigns.models import Campaign
from app.ai_engine.rules.base import BaseRule
from app.ai_engine.models.action_models import (
    AIAction,
    AIActionType,
    MetricEvidence,
    ConfidenceScore,
)


class SalesROASDropRule(BaseRule):
    """
    Phase 9.4 — Sales ROAS Drop Rule (Benchmark-Aware)

    Uses:
    - Aggregated campaign metrics (7D vs 30D)
    - Industry benchmark comparison (category-level)
    - Decay / fatigue signals
    """

    MIN_PROFITABLE_ROAS = 1.2
    ROAS_DROP_THRESHOLD = 0.75        # 25% drop vs self baseline
    BENCHMARK_ROAS_DELTA = 0.80       # 20% worse than industry avg

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: Dict,
    ) -> List[AIAction]:

        # -------------------------------------------------
        # Eligibility
        # -------------------------------------------------
        if campaign.objective.upper() not in (
            "SALES",
            "CONVERSIONS",
            "OUTCOME_SALES",
        ):
            return []

        if ai_context.get("status") == "insufficient_data":
            return []

        short_row = ai_context.get("short_window")
        long_row = ai_context.get("long_window")

        if not short_row or not long_row:
            return []

        short_roas = short_row.get("roas")
        long_roas = long_row.get("roas")

        if not short_roas or not long_roas:
            return []

        roas_ratio = short_roas / long_roas if long_roas else 1.0
        signals = ai_context.get("signals", {})

        # -------------------------------------------------
        # INDUSTRY BENCHMARK (PHASE 9.4)
        # -------------------------------------------------
        benchmark = await db.execute(
            text(
                """
                SELECT avg_roas
                FROM industry_benchmarks
                WHERE category = (
                    SELECT category
                    FROM campaign_category_map
                    WHERE campaign_id = :campaign_id
                )
                  AND objective_type = :objective
                  AND window_type = '7d'
                ORDER BY as_of_date DESC
                LIMIT 1
                """
            ),
            {
                "campaign_id": str(campaign.id),
                "objective": campaign.objective,
            },
        )

        benchmark_row = benchmark.fetchone()
        benchmark_roas = (
            float(benchmark_row.avg_roas)
            if benchmark_row and benchmark_row.avg_roas
            else None
        )

        worse_than_benchmark = (
            benchmark_roas
            and short_roas < benchmark_roas * self.BENCHMARK_ROAS_DELTA
        )

        # -------------------------------------------------
        # Decision logic
        # -------------------------------------------------
        if (
            short_roas < self.MIN_PROFITABLE_ROAS
            and roas_ratio < self.ROAS_DROP_THRESHOLD
        ):
            reason = "ROAS dropped compared to 30-day baseline."

            confidence = 0.75

            if signals.get("decay"):
                reason += " Performance decay detected."
                confidence += 0.05

            if worse_than_benchmark:
                reason += " Campaign is also underperforming industry benchmarks."
                confidence += 0.10

            return [
                AIAction(
                    campaign_id=campaign.id,
                    action_type=AIActionType.REDUCE_BUDGET,
                    summary=(
                        "Reduce budget: ROAS declined below profitable levels "
                        "relative to historical and industry benchmarks."
                    ),
                    metrics=[
                        MetricEvidence(
                            metric="roas",
                            window="7D",
                            value=round(short_roas, 3),
                            baseline=round(long_roas, 3),
                            delta_pct=round((roas_ratio - 1) * 100, 2),
                        ),
                    ],
                    confidence=ConfidenceScore(
                        score=min(confidence, 0.95),
                        reason=reason,
                    ),
                )
            ]

        return []
