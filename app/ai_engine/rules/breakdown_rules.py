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


# =========================================================
# BEST CREATIVE RULE
# =========================================================
class BestCreativeRule(BaseRule):
    """
    Phase 9.3.3 — Best Creative Intelligence

    Uses:
    - campaign_breakdown_aggregates
    - 7D window
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

        if ai_context.get("status") == "insufficient_data":
            return []

        result = await db.execute(
            """
            SELECT
                creative_id,
                impressions,
                conversions,
                roas,
                cpl,
                ctr
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

        if not best:
            return []

        if best.impressions < self.MIN_IMPRESSIONS or best.conversions < self.MIN_CONVERSIONS:
            return []

        metric = "roas" if best.roas is not None else "cpl"
        value = best.roas if best.roas is not None else best.cpl

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.SHIFT_CREATIVE,
                summary="One creative is clearly outperforming others.",
                breakdowns=[
                    BreakdownEvidence(
                        dimension="creative_id",
                        key=best.creative_id,
                        metrics=[
                            MetricEvidence(
                                metric=metric,
                                window="7D",
                                value=round(float(value), 3),
                            )
                        ],
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.85,
                    reason="High efficiency with sufficient volume over 7 days.",
                ),
            )
        ]


# =========================================================
# BEST PLACEMENT RULE
# =========================================================
class BestPlacementRule(BaseRule):
    """
    Phase 9.3.3 — Best Placement Intelligence
    """

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: Dict,
    ) -> List[AIAction]:

        result = await db.execute(
            """
            SELECT
                placement,
                impressions,
                conversions,
                roas,
                cpl
            FROM campaign_breakdown_aggregates
            WHERE campaign_id = :campaign_id
              AND window_type = '7d'
              AND placement IS NOT NULL
            ORDER BY
                roas DESC NULLS LAST,
                cpl ASC NULLS LAST
            LIMIT 1
            """,
            {"campaign_id": str(campaign.id)},
        )
        best = result.first()

        if not best or best.impressions < 300:
            return []

        metric = "roas" if best.roas is not None else "cpl"
        value = best.roas if best.roas is not None else best.cpl

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.SHIFT_PLACEMENT,
                summary="A specific placement is outperforming others.",
                breakdowns=[
                    BreakdownEvidence(
                        dimension="placement",
                        key=best.placement,
                        metrics=[
                            MetricEvidence(
                                metric=metric,
                                window="7D",
                                value=round(float(value), 3),
                            )
                        ],
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.78,
                    reason="Consistent performance advantage by placement.",
                ),
            )
        ]


# =========================================================
# BEST AUDIENCE SEGMENT RULE
# =========================================================
class BestAudienceSegmentRule(BaseRule):
    """
    Phase 9.3.3 — Best Region / Age / Gender Intelligence
    """

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: Dict,
    ) -> List[AIAction]:

        result = await db.execute(
            """
            SELECT
                region,
                age_group,
                gender,
                impressions,
                conversions,
                roas,
                cpl
            FROM campaign_breakdown_aggregates
            WHERE campaign_id = :campaign_id
              AND window_type = '7d'
              AND (region IS NOT NULL OR age_group IS NOT NULL OR gender IS NOT NULL)
            ORDER BY
                roas DESC NULLS LAST,
                cpl ASC NULLS LAST
            LIMIT 1
            """,
            {"campaign_id": str(campaign.id)},
        )
        best = result.first()

        if not best or best.impressions < 300:
            return []

        metric = "roas" if best.roas is not None else "cpl"
        value = best.roas if best.roas is not None else best.cpl

        key = " / ".join(
            filter(
                None,
                [best.region, best.age_group, best.gender],
            )
        )

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.SHIFT_AUDIENCE,
                summary="A specific audience segment is outperforming others.",
                breakdowns=[
                    BreakdownEvidence(
                        dimension="audience_segment",
                        key=key,
                        metrics=[
                            MetricEvidence(
                                metric=metric,
                                window="7D",
                                value=round(float(value), 3),
                            )
                        ],
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.75,
                    reason="Audience segment shows better efficiency over last 7 days.",
                ),
            )
        ]
