from typing import List, Dict

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

# 🔥 NEW — Industry benchmark intelligence
from app.ai_engine.services.campaign_vs_benchmark_service import (
    CampaignVsBenchmarkService,
)


class AIDecisionRunner:
    """
    FINAL — Phase 9.4 Decision Runner (LIVE, NO DB)

    - No DB writes
    - No persistence
    - Uses breakdown intelligence
    - Uses category intelligence
    - Uses industry benchmark intelligence (NEW)
    """

    def __init__(self) -> None:
        self.rules = [
            # Campaign health
            LeadPerformanceDropRule(),
            SalesROASDropRule(),

            # Breakdown intelligence
            BestCreativeRule(),
            BestPlacementRule(),
            BestAudienceSegmentRule(),

            # Strategy intelligence
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

        for campaign in campaigns:
            # -------------------------------------------------
            # BASE AI CONTEXT (WINDOWED PERFORMANCE)
            # -------------------------------------------------
            ai_context: Dict = await ai_service.get_campaign_ai_score(
                campaign_id=str(campaign.id),
                short_window="7d",
                long_window="30d",
            )

            # -------------------------------------------------
            # 🔥 INDUSTRY BENCHMARK CONTEXT (PHASE 9.4)
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
