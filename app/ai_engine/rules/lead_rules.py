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


class LeadPerformanceDropRule(BaseRule):
    """
    Phase 12 — Lead Performance Drop Rule (Feedback-Calibrated)

    Uses:
    - Aggregated campaign metrics
    - Industry benchmark
    - Fatigue signals
    - Feedback-weighted confidence
    """

    CTR_DROP_THRESHOLD = 0.8        # 20% drop vs self baseline
    CPL_INCREASE_THRESHOLD = 25.0   # % increase vs self baseline
    BENCHMARK_CPL_DELTA = 1.20      # 20% worse than industry avg

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
            "LEAD",
            "LEAD_GENERATION",
            "OUTCOME_LEADS",
            "MESSAGES",
            "TRAFFIC",
        ):
            return []

        if ai_context.get("status") == "insufficient_data":
            return []

        short_row = ai_context.get("short_window")
        long_row = ai_context.get("long_window")

        if not short_row or not long_row:
            return []

        short_ctr = short_row.get("ctr")
        long_ctr = long_row.get("ctr")
        short_cpl = short_row.get("cpl")
        long_cpl = long_row.get("cpl")

        if not short_ctr or not long_ctr or not short_cpl or not long_cpl:
            return []

        ctr_ratio = short_ctr / long_ctr if long_ctr else 1.0
        cpl_change_pct = ((short_cpl - long_cpl) / long_cpl) * 100
        signals = ai_context.get("signals", {})

        # -------------------------------------------------
        # INDUSTRY BENCHMARK
        # -------------------------------------------------
        benchmark_result = await db.execute(
            text(
                """
                SELECT avg_cpl
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

        benchmark_row = benchmark_result.fetchone()
        benchmark_cpl = (
            float(benchmark_row.avg_cpl)
            if benchmark_row and benchmark_row.avg_cpl
            else None
        )

        worse_than_benchmark = (
            benchmark_cpl
            and short_cpl > benchmark_cpl * self.BENCHMARK_CPL_DELTA
        )

        # -------------------------------------------------
        # Decision logic
        # -------------------------------------------------
        if (
            ctr_ratio < self.CTR_DROP_THRESHOLD
            and cpl_change_pct >= self.CPL_INCREASE_THRESHOLD
        ):
            reason = "Lead efficiency dropped compared to 30-day baseline."
            base_confidence = 0.75

            explain_steps = [
                f"7D CTR = {round(short_ctr, 4)}",
                f"30D CTR = {round(long_ctr, 4)}",
                f"CTR change = {round((ctr_ratio - 1) * 100, 2)}%",
                f"7D CPL = {round(short_cpl, 2)}",
                f"30D CPL = {round(long_cpl, 2)}",
                f"CPL change = {round(cpl_change_pct, 2)}%",
            ]

            if signals.get("fatigue"):
                reason += " Fatigue signal detected."
                base_confidence += 0.05
                explain_steps.append("Fatigue detected from CTR trend")

            if worse_than_benchmark:
                reason += " Performance is worse than industry benchmark."
                base_confidence += 0.10
                explain_steps.append(
                    f"Industry benchmark CPL ≈ {round(benchmark_cpl, 2)}"
                )

            # -------------------------------------------------
            # Phase 12 — Feedback-calibrated confidence
            # -------------------------------------------------
            calibrated_confidence = await self.calibrate_confidence(
                db=db,
                base_score=min(base_confidence, 0.95),
                campaign_id=campaign.id,
                action_type=AIActionType.REDUCE_BUDGET.value,
            )

            action = AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.REDUCE_BUDGET,
                summary=(
                    "Reduce budget: CPL increased and CTR dropped "
                    "relative to historical and industry benchmarks."
                ),
                metrics=[
                    MetricEvidence(
                        metric="ctr",
                        window="7D",
                        value=round(short_ctr, 4),
                        baseline=round(long_ctr, 4),
                        delta_pct=round((ctr_ratio - 1) * 100, 2),
                        source="campaign",
                    ),
                    MetricEvidence(
                        metric="cpl",
                        window="7D",
                        value=round(short_cpl, 2),
                        baseline=round(long_cpl, 2),
                        delta_pct=round(cpl_change_pct, 2),
                        source="campaign",
                    ),
                    *(
                        [
                            MetricEvidence(
                                metric="industry_cpl",
                                window="7D",
                                value=round(benchmark_cpl, 2),
                                source="industry",
                            )
                        ]
                        if benchmark_cpl
                        else []
                    ),
                ],
                confidence=calibrated_confidence,
            )

            return [
                self.attach_explainability(
                    action,
                    steps=explain_steps,
                    benchmark_used=bool(benchmark_cpl),
                    trust_note=(
                        "Confirmed by industry benchmark"
                        if worse_than_benchmark
                        else "Based on campaign performance trend"
                    ),
                )
            ]

        return []
