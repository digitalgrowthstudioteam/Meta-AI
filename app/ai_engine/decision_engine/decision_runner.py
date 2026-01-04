from datetime import date
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIActionSet, AIAction
from app.ai_engine.decision_engine.campaign_decision_service import (
    CampaignDecisionService,
)


class AIDecisionRunner:
    """
    Phase 7 — LIVE AI Decision Runner

    Characteristics:
    - NO database writes
    - NO persistence
    - NO Meta mutation
    - Computes AI suggestions on demand
    """

    async def run_for_user(
        self,
        *,
        db: AsyncSession,
        user_id,
        as_of_date: date | None = None,
    ) -> List[AIActionSet]:
        """
        Generates LIVE AI suggestions for all AI-active campaigns
        visible to the user.
        """

        if as_of_date is None:
            as_of_date = date.today()

        # =========================================
        # 1️⃣ Fetch eligible AI-active campaigns
        # =========================================
        stmt = select(Campaign).where(
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
            Campaign.admin_locked.is_(False),
        )

        result = await db.execute(stmt)
        campaigns: List[Campaign] = result.scalars().all()

        # =========================================
        # 2️⃣ Generate AI actions (IN-MEMORY)
        # =========================================
        action_sets: Dict[str, AIActionSet] = {}

        for campaign in campaigns:
            action: AIAction | None = await CampaignDecisionService.decide_for_campaign(
                db=db,
                campaign=campaign,
                as_of_date=as_of_date,
            )

            if not action:
                continue

            # Group by campaign
            key = str(campaign.id)

            if key not in action_sets:
                action_sets[key] = AIActionSet(
                    campaign_id=campaign.id,
                    actions=[],
                )

            action_sets[key].actions.append(action)

        # =========================================
        # 3️⃣ Return LIVE AI output
        # =========================================
        return list(action_sets.values())
