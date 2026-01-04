from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction, AIActionSet
from app.ai_engine.rules.lead_rules import LeadPerformanceDropRule
from app.ai_engine.rules.sales_rules import SalesROASDropRule
from app.ai_engine.rules.breakdown_rules import BestCreativeRule
from app.ai_engine.rules.category_strategy_rules import (
    CategoryStrategyRule,
)
from app.ai_engine.campaign_ai_readiness_service import (
    CampaignAIReadinessService,
)


class AIDecisionRunner:
    """
    FINAL — Phase 9 Decision Runner (LIVE, NO DB)

    - No DB writes
    - No persistence
    - Uses Phase 7.3 AI intelligence
    - Uses Phase 9.5 category intelligence
    - Rules evaluated in-memory
    - Returns AIActionSet per campaign
    """

    def __init__(self) -> None:
        self.rules = [
            LeadPerformanceDropRule(),
            SalesROASDropRule(),
            BestCreativeRule(),
            CategoryStrategyRule(),  # 🧠 strategy-level intelligence
        ]

    async def run_for_user(
        self,
        *,
        db: AsyncSession,
        user_id,
    ) -> List[AIActionSet]:
        """
        Run AI rules for all AI-active campaigns
        visible to the logged-in user.
        """

        stmt = select(Campaign).where(
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
        )

        result = await db.execute(stmt)
        campaigns: List[Campaign] = result.scalars().all()

        ai_service = CampaignAIReadinessService(db)

        action_sets: List[AIActionSet] = []

        for campaign in campaigns:
            # -----------------------------------------
            # PHASE 7.3 INTELLIGENCE (ONCE PER CAMPAIGN)
            # -----------------------------------------
            ai_context: Dict = await ai_service.get_campaign_ai_score(
                campaign_id=str(campaign.id),
                short_window="7d",
                long_window="30d",
            )

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
