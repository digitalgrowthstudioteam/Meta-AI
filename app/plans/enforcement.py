from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.subscription_models import Subscription, SubscriptionAddon
from app.admin.models import GlobalSettings
from app.campaigns.models import Campaign, CampaignActionLog
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.plans.usage_override_service import UsageOverrideService


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

    # =====================================================
    # PHASE 9 — AD ACCOUNT LIMIT ENFORCEMENT (OPTION A)
    # =====================================================
    @staticmethod
    async def _count_selected_ad_accounts(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(UserMetaAdAccount.meta_ad_account_id)).where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
            )
        )
        return result.scalar_one() or 0

    @staticmethod
    async def assert_ad_account_allowed(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        """
        Called BEFORE selecting a new Ad Account.
        Now respects Phase-10 override (ad_accounts).
        """
        subscription = await PlanEnforcementService._get_active_subscription(
            db=db,
            user_id=user_id,
        )
        if not subscription:
            raise EnforcementError(
                code="NO_SUBSCRIPTION",
                message="No active plan.",
                action="UPGRADE_PLAN",
            )

        current = await PlanEnforcementService._count_selected_ad_accounts(
            db=db,
            user_id=user_id,
        )

        plan_default = getattr(subscription, "ad_account_limit_snapshot", 0)

        effective_limit = await UsageOverrideService.get_effective_limit(
            db=db,
            user_id=user_id,
            key="ad_accounts",
            plan_default=plan_default,
        )

        if current >= effective_limit:
            raise EnforcementError(
                code="AD_ACCOUNT_LIMIT_REACHED",
                message="Upgrade to connect more Ad Accounts.",
                action="UPGRADE_PLAN",
            )

    # =====================================================
    # USAGE COUNTERS (PHASE P2)
    # =====================================================
    @staticmethod
    async def _count_actions_today(
        db: AsyncSession,
        *,
        user_id: UUID,
        action_type: str,
    ) -> int:
        start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await db.execute(
            select(func.count(CampaignActionLog.id)).where(
                CampaignActionLog.user_id == user_id,
                CampaignActionLog.action_type == action_type,
                CampaignActionLog.created_at >= start,
            )
        )
        return result.scalar_one()

    @staticmethod
    async def _get_last_ai_action_time(
        db: AsyncSession,
        *,
        campaign_id: UUID,
    ) -> Optional[datetime]:
        result = await db.execute(
            select(CampaignActionLog.created_at)
            .where(
                CampaignActionLog.campaign_id == campaign_id,
                CampaignActionLog.actor_type == "ai",
            )
            .order_by(CampaignActionLog.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # =====================================================
    # ADDON SLOT RESERVATION
    # =====================================================
    @staticmethod
    async def _reserve_addon_slot(
        db: AsyncSession,
        *,
        subscription: Subscription,
        campaign: Campaign,
    ) -> Optional[SubscriptionAddon]:
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

    # =====================================================
    # MAIN AI ENFORCEMENT
    # =====================================================
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
                message="AI is disabled by admin.",
                action="CONTACT_SUPPORT",
            )

        if settings:
            if (
                not settings.expansion_mode_enabled
                and getattr(campaign, "ai_mode", None) == "EXPANSION"
            ):
                raise EnforcementError(
                    code="EXPANSION_DISABLED",
                    message="Expansion mode disabled by admin.",
                    action="CONTACT_SUPPORT",
                )

            if (
                not settings.fatigue_mode_enabled
                and getattr(campaign, "ai_mode", None) == "FATIGUE"
            ):
                raise EnforcementError(
                    code="FATIGUE_DISABLED",
                    message="Fatigue mode disabled by admin.",
                    action="CONTACT_SUPPORT",
                )

            if (
                not settings.auto_pause_enabled
                and getattr(campaign, "auto_pause_enabled", False)
            ):
                raise EnforcementError(
                    code="AUTO_PAUSE_DISABLED",
                    message="Auto-pause disabled by admin.",
                    action="CONTACT_SUPPORT",
                )

            if (
                not settings.confidence_gating_enabled
                and getattr(campaign, "requires_confidence", False)
            ):
                raise EnforcementError(
                    code="CONFIDENCE_GATING_DISABLED",
                    message="Confidence gating disabled by admin.",
                    action="CONTACT_SUPPORT",
                )

        # AI THROTTLING
        if settings:
            if settings.max_optimizations_per_day:
                used = await PlanEnforcementService._count_actions_today(
                    db=db,
                    user_id=user_id,
                    action_type="optimization",
                )
                if used >= settings.max_optimizations_per_day:
                    raise EnforcementError(
                        code="OPTIMIZATION_LIMIT_REACHED",
                        message="Daily optimization limit reached.",
                        action="WAIT",
                    )

            if settings.max_expansions_per_day:
                used = await PlanEnforcementService._count_actions_today(
                    db=db,
                    user_id=user_id,
                    action_type="expansion",
                )
                if used >= settings.max_expansions_per_day:
                    raise EnforcementError(
                        code="EXPANSION_LIMIT_REACHED",
                        message="Daily expansion limit reached.",
                        action="WAIT",
                    )

            if settings.ai_refresh_frequency_minutes:
                last_run = (
                    await PlanEnforcementService._get_last_ai_action_time(
                        db=db,
                        campaign_id=campaign.id,
                    )
                )
                if last_run:
                    next_allowed = last_run + timedelta(
                        minutes=settings.ai_refresh_frequency_minutes
                    )
                    if datetime.utcnow() < next_allowed:
                        raise EnforcementError(
                            code="AI_REFRESH_COOLDOWN",
                            message="AI refresh cooldown active.",
                            action="WAIT",
                        )

        subscription = await PlanEnforcementService._get_active_subscription(
            db=db, user_id=user_id
        )
        if not subscription:
            raise EnforcementError(
                code="NO_SUBSCRIPTION",
                message="No active plan.",
                action="UPGRADE_PLAN",
            )

        base_limit = subscription.ai_campaign_limit_snapshot or 0
        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db=db, user_id=user_id
        )

        # OVERRIDE integration for AI campaigns
        effective_limit = await UsageOverrideService.get_effective_limit(
            db=db,
            user_id=user_id,
            key="campaigns",
            plan_default=base_limit,
        )

        if active_count < effective_limit:
            return

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
                    after_state={"addon_id": str(addon.id)},
                    reason="Addon slot consumed",
                )
            )
            return

        raise EnforcementError(
            code="AI_LIMIT_REACHED",
            message="AI campaign limit reached.",
            action="BUY_SLOTS",
        )

    # =====================================================
    # STATUS HELPERS
    # =====================================================
    @staticmethod
    async def get_ai_limit_status(db: AsyncSession, *, user_id: UUID) -> dict:
        settings = await PlanEnforcementService._get_global_settings(db)

        subscription = await PlanEnforcementService._get_active_subscription(
            db=db, user_id=user_id
        )

        active = (
            await PlanEnforcementService._count_active_ai_campaigns(
                db=db, user_id=user_id
            )
            if subscription
            else 0
        )

        return {
            "ai_enabled": settings.ai_globally_enabled if settings else True,
            "expansion_mode": settings.expansion_mode_enabled if settings else True,
            "fatigue_mode": settings.fatigue_mode_enabled if settings else True,
            "auto_pause": settings.auto_pause_enabled if settings else True,
            "confidence_gating": settings.confidence_gating_enabled if settings else True,
            "active_campaigns": active,
            "max_optimizations_per_day": settings.max_optimizations_per_day if settings else None,
            "max_expansions_per_day": settings.max_expansions_per_day if settings else None,
            "ai_refresh_frequency_minutes": settings.ai_refresh_frequency_minutes if settings else None,
        }
