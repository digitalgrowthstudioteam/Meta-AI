from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    # LIST CAMPAIGNS — COOKIE MODE (NO DB is_selected)
    # =====================================================
    @staticmethod
    async def list_campaigns_with_visibility(
        db: AsyncSession,
        *,
        user_id: UUID,
        ad_account_ids: list[UUID],
    ) -> list[Campaign]:
        if not ad_account_ids:
            return []

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
                Campaign.ad_account_id.in_(ad_account_ids),
                Campaign.is_archived.is_(False),
            )
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # SYNC CAMPAIGNS FROM META — COOKIE MODE
    # =====================================================
    @staticmethod
    async def sync_from_meta(
        db: AsyncSession,
        *,
        user_id: UUID,
        ad_account_ids: list[UUID],
    ) -> list[Campaign]:

        if not ad_account_ids:
            logger.warning("sync_from_meta: no accounts provided for user=%s", user_id)
            return []

        result = await db.execute(
            select(MetaAdAccount)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                MetaAdAccount.id.in_(ad_account_ids),
                MetaAdAccount.is_active.is_(True),
            )
        )
        ad_accounts = result.scalars().all()

        if not ad_accounts:
            logger.warning("No owned ad accounts found for user=%s", user_id)
            return []

        synced: list[Campaign] = []

        for ad_account in ad_accounts:
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
                continue

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
                    # system actor trace
                    user_id=campaign.ad_account_id,
                    actor_type="system",
                    action_type="manual_expiry",
                    before_state=before_state,
                    after_state=after_state,
                    reason="Manual campaign expired",
                )
            )

    # =====================================================
    # AI TOGGLE — PLAN ENFORCED + TRANSACTION SAFE
    # =====================================================
    @staticmethod
    async def toggle_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign_id: UUID,
        enable: bool,
    ) -> Campaign:

        # 1) Ensure ownership
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
            )
            .with_for_update()  # prevent toggle race
        )

        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found or not owned by user")

        # 2) Manual validity enforcement
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

        before_state = {"ai_active": campaign.ai_active}

        # 3) PLAN ENFORCEMENT — only on enabling
        if enable and not campaign.ai_active:
            await PlanEnforcementService.assert_ai_allowed(
                db=db,
                user_id=user_id,
            )

        # 4) State mutation
        campaign.ai_active = enable
        campaign.ai_activated_at = datetime.utcnow() if enable else None
        campaign.ai_deactivated_at = None if enable else datetime.utcnow()

        after_state = {"ai_active": campaign.ai_active}

        # 5) Audit log
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

        # 6) Final commit
        await db.commit()
        await db.refresh(campaign)
        return campaign
