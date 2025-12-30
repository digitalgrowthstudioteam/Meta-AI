from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.campaigns.models import Campaign
from app.plans.enforcement import (
    PlanEnforcementService,
    EnforcementError,
)


class CampaignService:
    """
    Campaign business logic layer.

    🔒 Enforcement is applied HERE.
    - No UI bypass
    - No AI bypass
    - No admin bypass (unless via override table)
    """

    @staticmethod
    async def list_campaigns(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:
        stmt = select(Campaign).where(Campaign.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def toggle_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign_id: UUID,
        enable: bool,
    ) -> Campaign:
        stmt = select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == user_id,
        )
        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        # =====================================================
        # 🔐 ENFORCEMENT (ONLY WHEN ENABLING AI)
        # =====================================================
        if enable and not campaign.ai_active:
            try:
                await PlanEnforcementService.can_activate_ai(
                    db=db,
                    user_id=user_id,
                )
            except EnforcementError as e:
                # IMPORTANT:
                # - Do NOT mutate campaign
                # - Do NOT partially commit
                raise ValueError(str(e))

        # =====================================================
        # APPLY TOGGLE
        # =====================================================
        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None

        await db.commit()
        await db.refresh(campaign)

        return campaign
