from datetime import date
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIActionSet
from app.ai_engine.decision_engine.campaign_decision_service import (
    CampaignDecisionService,
)


    @staticmethod
    async def run_for_user(
        *,
        db: AsyncSession,
        user_id,
    ) -> List[AIActionSet]:
        """
        Runs AI decision engine for all AI-active campaigns
        belonging to a specific user.

        Returns:
            List of AIActionSet (campaign-wise suggestions)
        """

        # Fetch user-visible AI-active campaigns
        stmt = (
            select(Campaign)
            .where(
                Campaign.ai_active.is_(True),
                Campaign.is_archived.is_(False),
                Campaign.admin_locked.is_(False),
            )
        )

        result = await db.execute(stmt)
        campaigns = result.scalars().all()

        action_sets: List[AIActionSet] = []

        for campaign in campaigns:
            actions = await CampaignDecisionService.decide_for_campaign(
                db=db,
                campaign=campaign,
                as_of_date=date.today(),
            )

            if not actions:
                continue

            action_sets.append(
                AIActionSet(
                    campaign_id=campaign.id,
                    actions=actions,
                )
            )

        return action_sets
