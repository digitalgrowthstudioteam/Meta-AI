from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.campaigns.models import Campaign
from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics
from app.ai_engine.rules.base import BaseRule
from app.ai_engine.models.action_models import (
    AIAction,
    AIActionType,
    MetricEvidence,
    ConfidenceScore,
)


class SalesROASDropRule(BaseRule):
    """
    Detect ROAS drop for sales campaigns.
    """

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
    ) -> List[AIAction]:

        if campaign.objective.upper() not in ("SALES", "CONVERSIONS", "OUTCOME_SALES"):
            return []

        stmt = select(func.avg(CampaignDailyMetrics.roas)).where(
            CampaignDailyMetrics.campaign_id == campaign.id,
        )
        result = await db.execute(stmt)
        avg_roas = result.scalar() or 0

        if avg_roas >= 1.2:
            return []

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.REDUCE_BUDGET,
                summary="ROAS dropped below profitability threshold",
                metrics=[
                    MetricEvidence(
                        metric="roas",
                        window="7D",
                        value=avg_roas,
                        baseline=1.2,
                        delta_pct=((avg_roas - 1.2) / 1.2) * 100,
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.75,
                    reason="ROAS consistently below profitable range",
                ),
            )
        ]
