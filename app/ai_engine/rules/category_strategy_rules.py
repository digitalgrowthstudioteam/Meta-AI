from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.campaigns.models import Campaign
from app.ai_engine.rules.base import BaseRule
from app.ai_engine.models.action_models import (
    AIAction,
    AIActionType,
    BreakdownEvidence,
    MetricEvidence,
    ConfidenceScore,
)
from app.ai_engine.models.campaign_category_map import CampaignCategoryMap
from app.ai_engine.models.ml_category_breakdown_stats import (
    MLCategoryBreakdownStat,
)


class CategoryStrategyRule(BaseRule):
    """
    Strategy-level AI guidance based on global category intelligence.

    - Uses aggregated cross-user data
    - NO execution
    - NO campaign mutation
    - Informational only
    """

    MIN_CONFIDENCE = 0.70
    MAX_RECOMMENDATIONS = 3

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
        ai_context: dict,
    ) -> List[AIAction]:

        # --------------------------------------------------
        # Resolve campaign category
        # --------------------------------------------------
        result = await db.execute(
            select(CampaignCategoryMap).where(
                CampaignCategoryMap.campaign_id == campaign.id
            )
        )
        category_map = result.scalar_one_or_none()

        if not category_map or category_map.confidence_score < self.MIN_CONFIDENCE:
            return []

        category = category_map.final_category

        # --------------------------------------------------
        # Fetch top-performing category breakdowns
        # --------------------------------------------------
        result = await db.execute(
            select(MLCategoryBreakdownStat)
            .where(
                MLCategoryBreakdownStat.business_category == category,
                MLCategoryBreakdownStat.confidence_score >= self.MIN_CONFIDENCE,
            )
            .order_by(
                desc(MLCategoryBreakdownStat.avg_roas),
                desc(MLCategoryBreakdownStat.confidence_score),
            )
            .limit(self.MAX_RECOMMENDATIONS)
        )

        rows = result.scalars().all()
        if not rows:
            return []

        # --------------------------------------------------
        # Build breakdown evidence
        # --------------------------------------------------
        breakdowns: List[BreakdownEvidence] = []

        for row in rows:
            dimension_parts = []
            if row.age_range:
                dimension_parts.append(f"Age {row.age_range}")
            if row.gender:
                dimension_parts.append(row.gender)
            if row.city:
                dimension_parts.append(row.city)
            if row.placement:
                dimension_parts.append(row.placement)
            if row.device:
                dimension_parts.append(row.device)

            breakdowns.append(
                BreakdownEvidence(
                    dimension=" | ".join(dimension_parts) or "General",
                    key=category,
                    metrics=[
                        MetricEvidence(
                            metric="roas",
                            window=row.window_type,
                            value=float(row.avg_roas) if row.avg_roas else 0.0,
                        ),
                        MetricEvidence(
                            metric="sample_size",
                            window=row.window_type,
                            value=float(row.sample_size),
                        ),
                    ],
                )
            )

        # --------------------------------------------------
        # Return strategy-only AI action
        # --------------------------------------------------
        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.NO_ACTION,
                summary=(
                    f"Based on aggregated data from similar {category} businesses, "
                    "campaigns typically perform best with the audience and placement "
                    "segments shown below."
                ),
                breakdowns=breakdowns,
                confidence=ConfidenceScore(
                    score=min(1.0, sum(r.confidence_score for r in rows) / len(rows)),
                    reason=(
                        "Derived from high-confidence, cross-user category performance "
                        "data with sufficient sample size."
                    ),
                ),
                is_auto_applicable=False,
            )
        ]
