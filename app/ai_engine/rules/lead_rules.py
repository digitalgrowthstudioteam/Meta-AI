from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics
from app.ai_engine.rules.base import BaseRule
from app.ai_engine.models.action_models import (
    AIAction,
    AIActionType,
    MetricEvidence,
    ConfidenceScore,
)


class LeadPerformanceDropRule(BaseRule):
    """
    Rule:
    - Detect lead campaign performance deterioration
    - Uses short vs stable window comparison
    - Suggests PAUSE or BUDGET REDUCTION
    """

    CTR_MIN = 0.8          # %
    CPL_INCREASE_PCT = 25  # %

    async def evaluate(
        self,
        *,
        db: AsyncSession,
        campaign: Campaign,
    ) -> List[AIAction]:

        # Only lead-type campaigns
        if campaign.objective.upper() not in (
            "LEAD",
            "LEAD_GENERATION",
            "OUTCOME_LEADS",
            "MESSAGES",
            "TRAFFIC",  # treated as leads (as per your requirement)
        ):
            return []

        # Fetch recent metrics (3D vs 14D)
        stmt = select(
            CampaignDailyMetrics
        ).where(
            CampaignDailyMetrics.campaign_id == campaign.id
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return []

        # Simple window split (safe, explainable)
        rows_sorted = sorted(rows, key=lambda r: r.metric_date, reverse=True)

        short = rows_sorted[:3]
        stable = rows_sorted[:14]

        def avg(values):
            vals = [v for v in values if v is not None]
            return sum(vals) / len(vals) if vals else None

        short_ctr = avg([r.ctr for r in short])
        short_cpl = avg([r.cpl for r in short])
        stable_cpl = avg([r.cpl for r in stable])

        if not short_cpl or not stable_cpl:
            return []

        cpl_change_pct = ((short_cpl - stable_cpl) / stable_cpl) * 100

        if (
            short_ctr is not None
            and short_ctr < self.CTR_MIN
            and cpl_change_pct > self.CPL_INCREASE_PCT
        ):
            return [
                AIAction(
                    campaign_id=campaign.id,
                    action_type=AIActionType.REDUCE_BUDGET,
                    summary=(
                        "Lead performance declined: CTR dropped and CPL increased "
                        "over the last few days."
                    ),
                    metrics=[
                        MetricEvidence(
                            metric="ctr",
                            window="3D",
                            value=short_ctr,
                        ),
                        MetricEvidence(
                            metric="cpl",
                            window="3D",
                            value=short_cpl,
                            baseline=stable_cpl,
                            delta_pct=round(cpl_change_pct, 2),
                        ),
                    ],
                    confidence=ConfidenceScore(
                        score=0.75,
                        reason=(
                            "Consistent CTR drop and CPL increase compared to "
                            "14-day baseline."
                        ),
                    ),
                )
            ]

        return []
