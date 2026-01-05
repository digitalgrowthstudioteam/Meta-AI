from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime
import logging

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.campaigns.meta_client import MetaCampaignClient
from app.plans.enforcement import (
    PlanEnforcementService,
    EnforcementError,
)

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Campaign business logic layer.
    """

    # =====================================================
    # LIST CAMPAIGNS + CATEGORY VISIBILITY (PHASE 9.2)
    # =====================================================
    @staticmethod
    async def list_campaigns_with_visibility(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:
        stmt = (
            select(Campaign)
            .options(selectinload(Campaign.category_map))
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
                Campaign.is_archived.is_(False),
            )
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # SYNC CAMPAIGNS FROM META (PHASE 5 — HARDENED)
    # =====================================================
    @staticmethod
    async def sync_from_meta(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:

        stmt = (
            select(MetaAdAccount)
            .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
                MetaAdAccount.is_active.is_(True),
            )
        )

        result = await db.execute(stmt)
        ad_account = result.scalar_one_or_none()

        if not ad_account:
            logger.warning("No selected ad account for user=%s", user_id)
            return []

        try:
            meta_campaigns = await MetaCampaignClient.fetch_campaigns(
                ad_account=ad_account,
            )
        except Exception as e:
            logger.error(
                "Meta sync failed for ad_account=%s : %s",
                ad_account.meta_account_id,
                str(e),
            )
            return []

        synced: list[Campaign] = []

        for meta in meta_campaigns:
            stmt = select(Campaign).where(
                Campaign.meta_campaign_id == meta["id"],
                Campaign.ad_account_id == ad_account.id,
            )
            result = await db.execute(stmt)
            campaign = result.scalar_one_or_none()

            if campaign:
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

            synced.append(campaign)

        await db.commit()
        return synced

    # =====================================================
    # AI TOGGLE (PHASE 5.2 — HARD LIMIT, RACE SAFE)
    # =====================================================
    @staticmethod
    async def toggle_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign_id: UUID,
        enable: bool,
    ) -> Campaign:

        # 🔒 Lock campaign row
        stmt = (
            select(Campaign)
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
            .where(
                Campaign.id == campaign_id,
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
            )
            .with_for_update()
        )

        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        # -------------------------------------------------
        # ENABLE AI — STRICT PLAN ENFORCEMENT
        # -------------------------------------------------
        if enable and not campaign.ai_active:
            # Global plan validity (expiry / suspension / admin kill)
            await PlanEnforcementService.assert_ai_allowed(
                db=db,
                user_id=user_id,
            )

            # Count active AI campaigns (locked scope)
            count_stmt = (
                select(func.count(Campaign.id))
                .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
                .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
                .where(
                    UserMetaAdAccount.user_id == user_id,
                    UserMetaAdAccount.is_selected.is_(True),
                    Campaign.ai_active.is_(True),
                )
                .with_for_update()
            )
            count_result = await db.execute(count_stmt)
            active_count = count_result.scalar_one()

            allowed = await PlanEnforcementService.get_ai_campaign_limit(
                db=db,
                user_id=user_id,
            )

            if active_count >= allowed:
                raise EnforcementError(
                    code="AI_CAMPAIGN_LIMIT_REACHED",
                    message=(
                        f"AI campaign limit reached "
                        f"({allowed}). Upgrade plan or buy add-ons."
                    ),
                )

        # -------------------------------------------------
        # APPLY TOGGLE
        # -------------------------------------------------
        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None
        campaign.ai_deactivated_at = None if enable else datetime.utcnow()

        await db.commit()
        await db.refresh(campaign)
        return campaign
