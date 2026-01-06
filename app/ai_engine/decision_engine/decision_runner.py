from typing import List, Dict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction, AIActionSet

from app.ai_engine.rules.lead_rules import LeadPerformanceDropRule
from app.ai_engine.rules.sales_rules import SalesROASDropRule
from app.ai_engine.rules.breakdown_rules import (
    BestCreativeRule,
    BestPlacementRule,
    BestAudienceSegmentRule,
)
from app.ai_engine.rules.category_strategy_rules import CategoryStrategyRule

from app.ai_engine.campaign_ai_readiness_service import (
    CampaignAIReadinessService,
)

from app.ai_engine.services.campaign_vs_benchmark_service import (
    CampaignVsBenchmarkService,
)

from app.ai_engine.services.user_trust_service import UserTrustService


# =====================================================
# PHASE 21 — CONFIDENCE BANDS (LOCKED)
# =====================================================
CONFIDENCE_BANDS = {
    "LOW": 0.60,       # Below this → suppressed
    "MEDIUM": 0.75,    # Visible but flagged
    "HIGH": 0.90,      # Strong recommendation
}


class AIDecisionRunner:
    """
    FINAL — Phase 21 Decision Runner (CONFIDENCE-GATED)

    - No DB writes
    - No Meta mutation
    - Hard confidence thresholds
    - Trust-adjusted + explainable
    """

    def __init__(self) -> None:
        self.rules = [
            LeadPerformanceDropRule(),
            SalesROASDropRule(),
            BestCreativeRule(),
            BestPlacementRule(),
            BestAudienceSegmentRule(),
            CategoryStrategyRule(),
        ]

    async def run_for_user(
        self,
        *,
        db: AsyncSession,
        user_id,
    ) -> List[AIActionSet]:

        # -------------------------------------------------
        # USER TRUST (ONCE PER REQUEST)
        # -------------------------------------------------
        user_trust_score, trust_reason = await UserTrustService.get_user_trust_score(
            db=db,
            user_id=user_id,
        )

        stmt = select(Campaign).where(
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
        )

        result = await db.execute(stmt)
        campaigns: List[Campaign] = result.scalars().all()

        ai_service = CampaignAIReadinessService(db)
        benchmark_service = CampaignVsBenchmarkService(db)

        action_sets: List[AIActionSet] = []
        now = datetime.utcnow()

        for campaign in campaigns:
            # -------------------------------------------------
            # HARD EXECUTION LOCKS
            # -------------------------------------------------
            if campaign.ai_execution_locked:
                continue

            if campaign.ai_execution_window_start and now < campaign.ai_execution_window_start:
                continue

            if campaign.ai_execution_window_end and now > campaign.ai_execution_window_end:
                continue

            # -------------------------------------------------
            # AI CONTEXT
            # -------------------------------------------------
            ai_context: Dict = await ai_service.get_campaign_ai_score(
                campaign_id=str(campaign.id),
                short_window="7d",
                long_window="30d",
            )

            benchmark_context = await benchmark_service.compare(
                campaign_id=str(campaign.id),
                window_type="30d",
            )

            ai_context["industry_benchmark"] = benchmark_context

            actions: List[AIAction] = []

            for rule in self.rules:
                rule_actions = await rule.evaluate(
                    db=db,
                    campaign=campaign,
                    ai_context=ai_context,
                )

                for action in rule_actions:
                    # -----------------------------------------
                    # APPLY USER TRUST
                    # -----------------------------------------
                    base_score = action.confidence.score
                    adjusted_score = round(
                        min(
                            1.0,
                            max(0.0, base_score * (0.8 + (user_trust_score * 0.4))),
                        ),
                        2,
                    )

                    # -----------------------------------------
                    # CONFIDENCE BAND ASSIGNMENT
                    # -----------------------------------------
                    if adjusted_score >= CONFIDENCE_BANDS["HIGH"]:
                        band = "HIGH"
                    elif adjusted_score >= CONFIDENCE_BANDS["MEDIUM"]:
                        band = "MEDIUM"
                    else:
                        band = "LOW"

                    # -----------------------------------------
                    # HARD THRESHOLD ENFORCEMENT
                    # -----------------------------------------
                    if band == "LOW":
                        continue  # suppressed completely

                    action.confidence.score = adjusted_score
                    action.confidence.band = band
                    action.confidence.reason += (
                        f" | Trust-adjusted ({trust_reason})"
                        f" | Confidence band: {band}"
                    )

                    actions.append(action)

            if actions:
                action_sets.append(
                    AIActionSet(
                        campaign_id=campaign.id,
                        actions=actions,
                    )
                )

        return action_sets
