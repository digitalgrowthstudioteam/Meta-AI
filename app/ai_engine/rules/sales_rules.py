from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

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
    Phase 9.4 — Industry-Aware Sales ROAS Drop Rule

    Uses:
    - Aggregated campaign metrics (7D vs 30D)
    - Industry benchmark comparison (30D)
    - Decay / fatigue signals
    """

    MIN_PROFITABLE_ROAS = 1.2
    ROAS_DROP_THRESHOLD = 0.75  # 25% drop vs baseline
    INDUSTRY_UNDERPERFORM_THRESHOLD = -20.0  # % vs industry avg

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
        # 🔥 Industry benchmark context (Phase 9.4)
        # -------------------------------------------------
        benchmark_ctx = ai_context.get("industry_benchmark", {})
        benchmark_metrics = benchmark_ctx.get("metrics", {})
        roas_benchmark = benchmark_metrics.get("roas")

        industry_delta = None
        if roas_benchmark and roas_benchmark.get("delta_pct") is not None:
            industry_delta = roas_benchmark["delta_pct"]

        # -------------------------------------------------
        # Decision logic
        # -------------------------------------------------
        should_reduce = (
            short_roas < self.MIN_PROFITABLE_ROAS
            and roas_ratio < self.ROAS_DROP_THRESHOLD
        )

        industry_confirmed = (
            industry_delta is not None
            and industry_delta < self.INDUSTRY_UNDERPERFORM_THRESHOLD
        )

        if should_reduce:
            reason = "ROAS dropped compared to 30-day baseline."

            if signals.get("decay"):
                reason += " Performance decay detected."

            if industry_confirmed:
                reason += " Campaign is also underperforming industry benchmarks."

            confidence_score = 0.75
            if industry_confirmed:
                confidence_score = 0.9  # higher confidence with benchmark confirmation

            return [
                AIAction(
                    campaign_id=campaign.id,
                    action_type=AIActionType.REDUCE_BUDGET,
                    summary=(
                        "Reduce budget: ROAS declined below profitable levels "
                        "and is underperforming recent performance."
                    ),
                    metrics=[
                        MetricEvidence(
                            metric="roas",
                            window="7D",
                            value=round(short_roas, 3),
                            baseline=round(long_roas, 3),
                            delta_pct=round((roas_ratio - 1) * 100, 2),
                        ),
                        *(
                            [
                                MetricEvidence(
                                    metric="industry_roas_delta",
                                    window="30D",
                                    value=round(industry_delta, 2),
                                )
                            ]
                            if industry_confirmed
                            else []
                        ),
                    ],
                    confidence=ConfidenceScore(
                        score=confidence_score,
                        reason=reason,
                    ),
                )
            ]

        return []
