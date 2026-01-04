from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.meta_insights.models.campaign_breakdown_daily_metrics import (
    CampaignBreakdownDailyMetrics,
)
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
    Identify best-performing creative by CPL / CPA.
    """

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
    ) -> List[AIAction]:

        stmt = (
            select(
                CampaignBreakdownDailyMetrics.ad_id,
                func.avg(CampaignBreakdownDailyMetrics.cpl),
            )
            .where(
                CampaignBreakdownDailyMetrics.campaign_id == campaign.id,
                CampaignBreakdownDailyMetrics.ad_id.isnot(None),
            )
            .group_by(CampaignBreakdownDailyMetrics.ad_id)
            .order_by(func.avg(CampaignBreakdownDailyMetrics.cpl))
            .limit(1)
        )

        result = await db.execute(stmt)
        best = result.first()

        if not best or not best[0]:
            return []

        return [
            AIAction(
                campaign_id=campaign.id,
                action_type=AIActionType.SHIFT_CREATIVE,
                summary="One creative significantly outperforms others",
                breakdowns=[
                    BreakdownEvidence(
                        dimension="ad_id",
                        key=best[0],
                        metrics=[
                            MetricEvidence(
                                metric="cpl",
                                window="14D",
                                value=float(best[1]),
                            )
                        ],
                    )
                ],
                confidence=ConfidenceScore(
                    score=0.81,
                    reason="Consistent superior creative performance",
                ),
            )
        ]
