from datetime import date
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction, AIActionSet
from app.ai_engine.rules.lead_rules import LeadPerformanceDropRule
from app.ai_engine.rules.sales_rules import SalesROASDropRule
from app.ai_engine.rules.breakdown_rules import BestCreativeRule


class AIDecisionRunner:
    """
    FINAL — Phase 7 Decision Runner (LIVE, NO DB)

    - No DB writes
    - No persistence
    - Rules evaluated in-memory
    - Returns AIActionSet per campaign
    """

    def __init__(self) -> None:
        self.rules = [
            LeadPerformanceDropRule(),
            SalesROASDropRule(),
            BestCreativeRule(),
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

        action_sets: List[AIActionSet] = []

        for campaign in campaigns:
            actions: List[AIAction] = []

            for rule in self.rules:
                rule_actions = await rule.evaluate(
                    db=db,
                    campaign=campaign,
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
