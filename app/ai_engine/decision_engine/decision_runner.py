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


class AIDecisionRunner:
    """
    FINAL — Phase 11 Decision Runner (SAFE)

    - No DB writes
    - No Meta mutation
    - Respects execution locks & time windows
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
            # PHASE 11 — HARD EXECUTION LOCK
            # -------------------------------------------------
            if campaign.ai_execution_locked:
                continue

            if campaign.ai_execution_window_start and now < campaign.ai_execution_window_start:
                continue

            if campaign.ai_execution_window_end and now > campaign.ai_execution_window_end:
                continue

            # -------------------------------------------------
            # BASE AI CONTEXT
            # -------------------------------------------------
            ai_context: Dict = await ai_service.get_campaign_ai_score(
                campaign_id=str(campaign.id),
                short_window="7d",
                long_window="30d",
            )

            # -------------------------------------------------
            # INDUSTRY BENCHMARK CONTEXT
            # -------------------------------------------------
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
                actions.extend(rule_actions)

            if actions:
                action_sets.append(
                    AIActionSet(
                        campaign_id=campaign.id,
                        actions=actions,
                    )
                )

        return action_sets
