from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, date
import logging

from app.campaigns.models import Campaign, CampaignActionLog
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
    # LIST CAMPAIGNS — STRICT SELECTED AD ACCOUNT (LOCKED)
    # =====================================================
    @staticmethod
    async def list_campaigns_with_visibility(
        db: AsyncSession,
        *,
        user_id: UUID,
        ad_account_id: UUID,
    ) -> list[Campaign]:
        stmt = (
            select(Campaign)
            .options(selectinload(Campaign.category_map))
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
                Campaign.ad_account_id == ad_account_id,
                Campaign.is_archived.is_(False),
            )
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # SYNC CAMPAIGNS FROM META (SELECTED ACCOUNT ONLY)
    # =====================================================
    @staticmethod
    async def sync_from_meta(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Campaign]:

        stmt = (
            select(MetaAdAccount)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
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
    # MANUAL CAMPAIGN VALIDITY ENFORCEMENT
    # =====================================================
    @staticmethod
    async def enforce_manual_campaign_validity(
        db: AsyncSession,
        *,
        campaign: Campaign,
    ) -> None:
        if not campaign.is_manual:
            return

        today = date.today()

        if (
            campaign.manual_status == "active"
            and campaign.manual_valid_till
            and today > campaign.manual_valid_till
        ):
            before_state = {
                "manual_status": campaign.manual_status,
            }

            campaign.manual_status = "expired"
            campaign.ai_active = False
            campaign.ai_deactivated_at = datetime.utcnow()

            after_state = {
                "manual_status": campaign.manual_status,
            }

            db.add(
                CampaignActionLog(
                    campaign_id=campaign.id,
                    user_id=campaign.ad_account_id,  # system trace
                    actor_type="system",
                    action_type="manual_expiry",
                    before_state=before_state,
                    after_state=after_state,
                    reason="Manual campaign expired",
                )
            )

    # =====================================================
    # AI TOGGLE — STRICT AD ACCOUNT SCOPE
    # =====================================================
    @staticmethod
    async def toggle_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign_id: UUID,
        enable: bool,
    ) -> Campaign:

        stmt = (
            select(Campaign)
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
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

        # 🔒 Enforce manual validity
        await CampaignService.enforce_manual_campaign_validity(
            db=db,
            campaign=campaign,
        )

        if campaign.is_manual and campaign.manual_status != "active":
            raise EnforcementError(
                code="MANUAL_CAMPAIGN_INACTIVE",
                message="Manual campaign is not active.",
                action="RENEW_MANUAL",
            )

        before_state = {
            "ai_active": campaign.ai_active,
        }

        if enable and not campaign.ai_active:
            await PlanEnforcementService.assert_ai_allowed(
                db=db,
                user_id=user_id,
            )

        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None
        campaign.ai_deactivated_at = None if enable else datetime.utcnow()

        after_state = {
            "ai_active": campaign.ai_active,
        }

        db.add(
            CampaignActionLog(
                campaign_id=campaign.id,
                user_id=user_id,
                actor_type="user",
                action_type="ai_toggle",
                before_state=before_state,
                after_state=after_state,
                reason="User toggled AI",
            )
        )

        await db.commit()
        await db.refresh(campaign)
        return campaign
