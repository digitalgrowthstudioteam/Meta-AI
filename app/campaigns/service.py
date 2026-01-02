from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.campaigns.models import Campaign
from app.meta.models import MetaAdAccount
from app.campaigns.meta_client import MetaCampaignClient
from app.plans.enforcement import (
    PlanEnforcementService,
    EnforcementError,
)


class CampaignService:
    """
    Campaign business logic layer.

    Responsibilities:
    - Campaign visibility
    - Meta sync (read-only)
    - AI toggle orchestration
    - Enforcement gateway (Phase 7.3)
    """

    # =====================================================
    # LIST CAMPAIGNS (VISIBILITY)
    # =====================================================
    @staticmethod
    async def list_campaigns(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:
        """
        Returns campaigns owned by the user's Meta ad accounts.
        """
        stmt = (
            select(Campaign)
            .join(
                MetaAdAccount,
                Campaign.ad_account_id == MetaAdAccount.id,
            )
            .where(MetaAdAccount.user_id == user_id)
            .where(Campaign.is_archived.is_(False))
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # SYNC CAMPAIGNS FROM META (READ-ONLY, IDEMPOTENT)
    # =====================================================
    @staticmethod
    async def sync_from_meta(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:
        """
        Fetches ALL campaigns from Meta (read-only)
        and upserts them idempotently.

        No AI logic.
        No billing logic.
        No enforcement.
        """

        # 1️⃣ Get user's connected Meta ad accounts
        stmt = select(MetaAdAccount).where(
            MetaAdAccount.user_id == user_id,
            MetaAdAccount.is_active.is_(True),
        )
        result = await db.execute(stmt)
        ad_accounts = result.scalars().all()

        if not ad_accounts:
            return []

        synced_campaigns: list[Campaign] = []

        # 2️⃣ Fetch & upsert campaigns per ad account
        for ad_account in ad_accounts:
            meta_campaigns = await MetaCampaignClient.fetch_campaigns(
                ad_account=ad_account,
            )

            for meta in meta_campaigns:
                stmt = select(Campaign).where(
                    Campaign.meta_campaign_id == meta["id"],
                    Campaign.ad_account_id == ad_account.id,
                )
                result = await db.execute(stmt)
                campaign = result.scalar_one_or_none()

                if campaign:
                    # Update snapshot (idempotent)
                    campaign.name = meta["name"]
                    campaign.objective = meta["objective"]
                    campaign.status = meta["status"]
                    campaign.last_meta_sync_at = datetime.utcnow()
                else:
                    campaign = Campaign(
                        meta_campaign_id=meta["id"],
                        ad_account_id=ad_account.id,
                        name=meta["name"],
                        objective=meta["objective"],
                        status=meta["status"],
                        last_meta_sync_at=datetime.utcnow(),
                    )
                    db.add(campaign)

                synced_campaigns.append(campaign)

        await db.commit()

        return synced_campaigns

    # =====================================================
    # AI TOGGLE (ENFORCEMENT COMES NEXT PHASE)
    # =====================================================
    @staticmethod
    async def toggle_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign_id: UUID,
        enable: bool,
    ) -> Campaign:
        """
        Enables or disables AI for a campaign.

        Phase 7.3 will add:
        - Limits
        - Trial logic
        - Billing enforcement
        """

        stmt = (
            select(Campaign)
            .join(
                MetaAdAccount,
                Campaign.ad_account_id == MetaAdAccount.id,
            )
            .where(
                Campaign.id == campaign_id,
                MetaAdAccount.user_id == user_id,
            )
        )

        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        # =================================================
        # ENFORCEMENT (ONLY WHEN ENABLING)
        # =================================================
        if enable and not campaign.ai_active:
            try:
                await PlanEnforcementService.can_activate_ai(
                    db=db,
                    user_id=user_id,
                )
            except EnforcementError as e:
                raise ValueError(str(e))

        # =================================================
        # APPLY TOGGLE
        # =================================================
        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None
        campaign.ai_deactivated_at = None if enable else datetime.utcnow()

        await db.commit()
        await db.refresh(campaign)

        return campaign
