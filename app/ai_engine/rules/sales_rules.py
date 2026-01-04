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
    Phase 8 — AI-Aware Sales ROAS Drop Rule

    Uses:
    - Aggregated metrics only
    - 7D vs 30D ROAS comparison
    - AI signals: decay / fatigue
    """

    MIN_PROFITABLE_ROAS = 1.2
    ROAS_DROP_THRESHOLD = 0.75  # 25% drop vs baseline

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: Dict,
    ) -> List[AIAction]:

        # -------------------------------------------------
        # Campaign eligibility
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
        # Decision logic
        # -------------------------------------------------
        if (
            short_roas < self.MIN_PROFITABLE_ROAS
            and roas_ratio < self.ROAS_DROP_THRESHOLD
        ):
            reason = "ROAS dropped compared to 30-day baseline."

            if signals.get("decay"):
                reason += " Performance decay signal detected."

            return [
                AIAction(
                    campaign_id=campaign.id,
                    action_type=AIActionType.REDUCE_BUDGET,
                    summary=(
                        "Reduce budget: ROAS declined below profitable levels "
                        "in the last 7 days."
                    ),
                    metrics=[
                        MetricEvidence(
                            metric="roas",
                            window="7D",
                            value=round(short_roas, 3),
                            baseline=round(long_roas, 3),
                            delta_pct=round((roas_ratio - 1) * 100, 2),
                        )
                    ],
                    confidence=ConfidenceScore(
                        score=0.8,
                        reason=reason,
                    ),
                )
            ]

        return []
