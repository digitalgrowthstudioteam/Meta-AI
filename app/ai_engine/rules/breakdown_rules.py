from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign
from app.ai_engine.rules.base import BaseRule
from app.ai_engine.models.action_models import (
    AIAction,
    AIActionType,
    BreakdownEvidence,
    MetricEvidence,
    ConfidenceScore,
)


class BestCreativeRule(BaseRule):
    """
    Phase 8 — AI-Aware Best Creative Rule

    Uses:
    - Aggregated breakdown intelligence
    - 7D performance window
    - ROAS / CPL efficiency ranking
    """

    MIN_IMPRESSIONS = 500
    MIN_CONVERSIONS = 3

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: Dict,
    ) -> List[AIAction]:

        # Only run if campaign has sufficient data
        if ai_context.get("status") == "insufficient_data":
            return []

        # Pull ranked creatives from AI readiness service context
        # NOTE: AIDecisionRunner guarantees ai_context exists
        breakdowns = ai_context.get("breakdowns")

        # Fallback: query aggregates directly (safe & allowed)
        if not breakdowns:
            result = await db.execute(
                """
                SELECT
                    creative_id,
                    impressions,
                    clicks,
                    spend,
                    conversions,
                    ctr,
                    cpl,
                    cpa,
                    roas
                FROM campaign_breakdown_aggregates
                WHERE campaign_id = :campaign_id
                  AND window_type = '7d'
                  AND creative_id IS NOT NULL
                ORDER BY
                    roas DESC NULLS LAST,
                    cpl ASC NULLS LAST,
                    ctr DESC NULLS LAST
                LIMIT 1
                """,
                {"campaign_id": str(campaign.id)},
            )
            best = result.first()
        else:
            best = None

        if not best:
            return []

        creative_id = best.creative_id
        impressions = best.impressions or 0
        conversions = best.conversions or 0

        if impressions < self.MIN_IMPRESSIONS or conversions < self.MIN_CONVERSIONS:
            return []

        # Decide metric priority
        metric_name = "roas" if best.roas is not None else "cpl"
        metric_value = best.roas if best.roas is not None else best.cpl

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.SHIFT_CREATIVE,
                summary=(
                    "One creative is significantly outperforming others "
                    "and should receive more budget."
                ),
                breakdowns=[
                    BreakdownEvidence(
                        dimension="creative_id",
                        key=creative_id,
                        metrics=[
                            MetricEvidence(
                                metric=metric_name,
                                window="7D",
                                value=round(float(metric_value), 3),
                            )
                        ],
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.85,
                    reason=(
                        "Creative shows superior efficiency with sufficient "
                        "volume over the last 7 days."
                    ),
                ),
            )
        ]
