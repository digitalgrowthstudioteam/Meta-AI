from datetime import date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction
from app.ai_engine.decision_engine.campaign_decision_service import (
    CampaignDecisionService,
)


class AIDecisionRunner:
    """
    Orchestrates AI decision generation for campaigns.
    """

    @staticmethod
    async def run(
        *,
        db: AsyncSession,
        as_of_date: date,
    ) -> int:
        """
        Runs AI decision generation for all eligible campaigns.
        """

        stmt = select(Campaign).where(
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
            Campaign.admin_locked.is_(False),
        )

        result = await db.execute(stmt)
        campaigns: List[Campaign] = result.scalars().all()

        actions_created = 0

        for campaign in campaigns:
            ai_action = await CampaignDecisionService.decide_for_campaign(
                db=db,
                campaign=campaign,
                as_of_date=as_of_date,
            )

            if not ai_action:
                continue

            dedupe_stmt = select(AIAction).where(
                and_(
                    AIAction.campaign_id == ai_action.campaign_id,
                    AIAction.action_type == ai_action.action_type,
                    AIAction.time_window == ai_action.time_window,
                    AIAction.status == "SUGGESTED",
                )
            )

            dedupe_result = await db.execute(dedupe_stmt)
            existing = dedupe_result.scalar_one_or_none()

            if existing:
                continue

            db.add(ai_action)
            actions_created += 1

        await db.commit()
        return actions_created
