from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.subscription_models import Subscription, SubscriptionAddon
from app.admin.models import AdminOverride, GlobalSettings
from app.campaigns.models import Campaign, CampaignActionLog
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount


class EnforcementError(Exception):
    def __init__(self, *, code: str, message: str, action: str):
        self.code = code
        self.message = message
        self.action = action
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "action": self.action,
        }


class PlanEnforcementService:

    # =========================
    # INTERNAL LOADERS
    # =========================
    @staticmethod
    async def _get_global_settings(db: AsyncSession) -> Optional[GlobalSettings]:
        result = await db.execute(select(GlobalSettings).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_active_subscription(
        db: AsyncSession, user_id: UUID
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active"]),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_active_admin_override(
        db: AsyncSession, user_id: UUID
    ) -> Optional[AdminOverride]:
        now = datetime.utcnow()
        result = await db.execute(
            select(AdminOverride).where(
                AdminOverride.user_id == user_id,
                (AdminOverride.override_expires_at.is_(None))
                | (AdminOverride.override_expires_at > now),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _count_active_ai_campaigns(
        db: AsyncSession, user_id: UUID
    ) -> int:
        result = await db.execute(
            select(func.count(Campaign.id))
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
                Campaign.ai_active.is_(True),
                Campaign.is_archived.is_(False),
            )
        )
        return result.scalar_one()

    # =========================
    # SLOT RESERVATION (NEW)
    # =========================
    @staticmethod
    async def _reserve_addon_slot(
        db: AsyncSession,
        *,
        subscription: Subscription,
        campaign: Campaign,
    ) -> Optional[SubscriptionAddon]:
        """
        Atomically reserve ONE available addon slot and bind it to campaign.
        """
        now = datetime.utcnow()

        result = await db.execute(
            select(SubscriptionAddon)
            .where(
                SubscriptionAddon.subscription_id == subscription.id,
                SubscriptionAddon.expires_at > now,
                SubscriptionAddon.consumed_by_campaign_id.is_(None),
            )
            .order_by(SubscriptionAddon.purchased_at.asc())
            .with_for_update()
            .limit(1)
        )
        addon = result.scalar_one_or_none()

        if not addon:
            return None

        addon.consumed_by_campaign_id = campaign.id
        return addon

    # =========================
    # MAIN AI ENFORCEMENT
    # =========================
    @staticmethod
    async def assert_ai_allowed(
        db: AsyncSession,
        *,
        user_id: UUID,
        campaign: Campaign,
    ) -> None:
        settings = await PlanEnforcementService._get_global_settings(db)
        if settings and not settings.ai_globally_enabled:
            raise EnforcementError(
                code="AI_GLOBALLY_DISABLED",
                message="AI is temporarily disabled by admin.",
                action="CONTACT_SUPPORT",
            )

        subscription = await PlanEnforcementService._get_active_subscription(
            db=db, user_id=user_id
        )
        if not subscription:
            raise EnforcementError(
                code="NO_SUBSCRIPTION",
                message="No active plan found.",
                action="UPGRADE_PLAN",
            )

        now = datetime.utcnow()
        if subscription.ends_at and now > subscription.ends_at:
            raise EnforcementError(
                code="SUBSCRIPTION_EXPIRED",
                message="Your subscription has expired.",
                action="RENEW_PLAN",
            )

        base_limit = subscription.ai_campaign_limit_snapshot or 0
        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db=db, user_id=user_id
        )

        override = await PlanEnforcementService._get_active_admin_override(
            db=db, user_id=user_id
        )
        admin_extra = override.extra_ai_campaigns if override else 0

        effective_limit = base_limit + admin_extra

        # ---------------------------------
        # BASE PLAN LIMIT CHECK
        # ---------------------------------
        if active_count < effective_limit:
            return

        # ---------------------------------
        # TRY SLOT ADDON CONSUMPTION
        # ---------------------------------
        addon = await PlanEnforcementService._reserve_addon_slot(
            db=db,
            subscription=subscription,
            campaign=campaign,
        )

        if addon:
            db.add(
                CampaignActionLog(
                    campaign_id=campaign.id,
                    user_id=user_id,
                    actor_type="system",
                    action_type="slot_consumed",
                    before_state={},
                    after_state={
                        "subscription_addon_id": str(addon.id)
                    },
                    reason="AI slot consumed",
                )
            )
            return

        # ---------------------------------
        # HARD STOP
        # ---------------------------------
        raise EnforcementError(
            code="AI_LIMIT_REACHED",
            message="AI campaign limit reached.",
            action="BUY_SLOTS",
        )

    # =========================
    # SUBSCRIPTION EXPIRY
    # =========================
    @staticmethod
    async def enforce_subscription_expiry(db: AsyncSession) -> int:
        now = datetime.utcnow()
        result = await db.execute(
            select(Subscription).where(
                Subscription.status.in_(["trial", "active"]),
                Subscription.ends_at.is_not(None),
                Subscription.ends_at < now,
            )
        )
        expired_subs = result.scalars().all()
        affected = 0

        for sub in expired_subs:
            sub.status = "expired"
            sub.is_active = False

            camp_result = await db.execute(
                select(Campaign)
                .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
                .join(
                    UserMetaAdAccount,
                    UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
                )
                .where(
                    UserMetaAdAccount.user_id == sub.user_id,
                    Campaign.ai_active.is_(True),
                )
            )
            campaigns = camp_result.scalars().all()

            for campaign in campaigns:
                before_state = {"ai_active": True}
                campaign.ai_active = False
                campaign.ai_deactivated_at = now
                after_state = {"ai_active": False}

                db.add(
                    CampaignActionLog(
                        campaign_id=campaign.id,
                        user_id=sub.user_id,
                        actor_type="system",
                        action_type="subscription_expiry",
                        before_state=before_state,
                        after_state=after_state,
                        reason="Subscription expired",
                    )
                )
                affected += 1

        await db.commit()
        return affected

    # =========================
    # STATUS HELPERS
    # =========================
    @staticmethod
    async def get_ai_limit_status(db: AsyncSession, *, user_id: UUID) -> dict:
        settings = await PlanEnforcementService._get_global_settings(db)
        if settings and not settings.ai_globally_enabled:
            return {"allowed": False, "reason": "AI_GLOBALLY_DISABLED"}

        subscription = await PlanEnforcementService._get_active_subscription(
            db=db, user_id=user_id
        )
        if not subscription:
            return {"allowed": False, "reason": "NO_SUBSCRIPTION"}

        base_limit = subscription.ai_campaign_limit_snapshot or 0
        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db=db, user_id=user_id
        )

        override = await PlanEnforcementService._get_active_admin_override(
            db=db, user_id=user_id
        )
        admin_extra = override.extra_ai_campaigns if override else 0

        return {
            "allowed": active_count < (base_limit + admin_extra),
            "active": active_count,
            "limit": base_limit + admin_extra,
            "base_limit": base_limit,
            "admin_extra": admin_extra,
        }
