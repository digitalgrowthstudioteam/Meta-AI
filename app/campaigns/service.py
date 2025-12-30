from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.campaigns.models import Campaign


class CampaignService:
    """
    Campaign business logic layer.

    IMPORTANT:
    - No enforcement yet (STEP 8.5)
    - No AI logic
    - No Meta API
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

        # ⚠️ Enforcement will be called here in STEP 8.5

        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None

        await db.commit()
        await db.refresh(campaign)

        return campaign
