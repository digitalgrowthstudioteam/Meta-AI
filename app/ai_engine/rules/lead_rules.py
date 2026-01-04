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


class LeadPerformanceDropRule(BaseRule):
    """
    Phase 8 — AI-Aware Lead Performance Drop Rule

    Uses:
    - Aggregated metrics only (NO raw daily data)
    - 7D vs 30D comparison
    - AI signals: fatigue / decay
    """

    CTR_DROP_THRESHOLD = 0.8        # 20% drop
    CPL_INCREASE_THRESHOLD = 25.0   # %

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
            "LEAD",
            "LEAD_GENERATION",
            "OUTCOME_LEADS",
            "MESSAGES",
            "TRAFFIC",
        ):
            return []

        if ai_context.get("status") == "insufficient_data":
            return []

        short = ai_context.get("short_window")
        long = ai_context.get("long_window")

        short_metrics = ai_context.get("signals") is not None
        data = ai_context

        # Extract aggregated values
        short_data = ai_context.get("short_window")
        long_data = ai_context.get("long_window")

        # Defensive — but should exist if complete window
        short_cpl = ai_context.get("short_window") and ai_context.get("short_window")
        # Instead, read from aggregate payload
        short_row = ai_context.get("short_window")
        long_row = ai_context.get("long_window")

        short_cpl = ai_context.get("short_window") and ai_context.get("short_window")
        # Correct source
        short_cpl = ai_context.get("short_window")
        long_cpl = ai_context.get("long_window")

        # We actually rely on numeric fields from aggregates
        short_ctr = ai_context.get("short_window") and ai_context.get("short_window")
        long_ctr = ai_context.get("long_window") and ai_context.get("long_window")

        # Pull metrics safely
        short_ctr = ai_context.get("short_window") and ai_context["short_window"].get("ctr")
        long_ctr = ai_context.get("long_window") and ai_context["long_window"].get("ctr")

        short_cpl = ai_context.get("short_window") and ai_context["short_window"].get("cpl")
        long_cpl = ai_context.get("long_window") and ai_context["long_window"].get("cpl")

        if not short_cpl or not long_cpl or not short_ctr or not long_ctr:
            return []

        cpl_change_pct = ((short_cpl - long_cpl) / long_cpl) * 100
        ctr_ratio = short_ctr / long_ctr if long_ctr else 1.0

        signals = ai_context.get("signals", {})

        # -------------------------------------------------
        # Decision logic
        # -------------------------------------------------
        if (
            ctr_ratio < self.CTR_DROP_THRESHOLD
            and cpl_change_pct >= self.CPL_INCREASE_THRESHOLD
        ):
            reason = "Lead efficiency dropped compared to 30-day baseline."

            if signals.get("fatigue"):
                reason += " Fatigue signal detected."

            return [
                AIAction(
                    campaign_id=campaign.id,
                    action_type=AIActionType.REDUCE_BUDGET,
                    summary=(
                        "Reduce budget: CPL increased and CTR dropped in the last 7 days."
                    ),
                    metrics=[
                        MetricEvidence(
                            metric="ctr",
                            window="7D",
                            value=round(short_ctr, 4),
                            baseline=round(long_ctr, 4),
                            delta_pct=round((ctr_ratio - 1) * 100, 2),
                        ),
                        MetricEvidence(
                            metric="cpl",
                            window="7D",
                            value=round(short_cpl, 2),
                            baseline=round(long_cpl, 2),
                            delta_pct=round(cpl_change_pct, 2),
                        ),
                    ],
                    confidence=ConfidenceScore(
                        score=0.8,
                        reason=reason,
                    ),
                )
            ]

        return []
