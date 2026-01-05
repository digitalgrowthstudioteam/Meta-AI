from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.subscription_models import Subscription
from app.admin.models import AdminOverride
from app.campaigns.models import Campaign, CampaignActionLog
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount


# =========================================================
# STRUCTURED ENFORCEMENT ERROR
# =========================================================
class EnforcementError(Exception):
    """
    Structured enforcement error.
    Always UI-safe and action-driven.
    """

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
    """
    🔒 SINGLE SOURCE OF TRUTH FOR PLAN, EXPIRY & DOWNGRADE ENFORCEMENT
    """

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================
    @staticmethod
    async def _get_active_subscription(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[Subscription]:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["trial", "active"]),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_active_admin_override(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[AdminOverride]:
        now = datetime.utcnow()

        stmt = select(AdminOverride).where(
            AdminOverride.user_id == user_id,
            (
                AdminOverride.override_expires_at.is_(None)
                | (AdminOverride.override_expires_at > now)
            ),
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _count_active_ai_campaigns(
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        stmt = (
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

        result = await db.execute(stmt)
        return result.scalar_one()

    # =====================================================
    # AI ACTIVATION GATE
    # =====================================================
    @staticmethod
    async def assert_ai_allowed(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        subscription = await PlanEnforcementService._get_active_subscription(
            db=db,
            user_id=user_id,
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

        override = await PlanEnforcementService._get_active_admin_override(
            db=db,
            user_id=user_id,
        )

        addon_extra = override.extra_ai_campaigns if override else 0
        effective_limit = base_limit + addon_extra

        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db=db,
            user_id=user_id,
        )

        if active_count >= effective_limit:
            if addon_extra > 0:
                raise EnforcementError(
                    code="AI_ADDON_LIMIT_REACHED",
                    message=f"AI add-on limit reached ({effective_limit}).",
                    action="BUY_ADDON",
                )

            raise EnforcementError(
                code="AI_PLAN_LIMIT_REACHED",
                message=f"AI campaign limit reached ({effective_limit}).",
                action="UPGRADE_PLAN",
            )

    # =====================================================
    # PHASE 12 — CRON ENFORCEMENT (EXPIRY + DOWNGRADE)
    # =====================================================
    @staticmethod
    async def enforce_subscription_expiry(
        db: AsyncSession,
    ) -> int:
        """
        CRON-SAFE:
        - Marks expired subscriptions
        - Disables AI across all campaigns
        - Creates audit logs
        """

        now = datetime.utcnow()

        stmt = select(Subscription).where(
            Subscription.status.in_(["trial", "active"]),
            Subscription.ends_at.is_not(None),
            Subscription.ends_at < now,
        )
        result = await db.execute(stmt)
        expired_subs = result.scalars().all()

        affected = 0

        for sub in expired_subs:
            sub.status = "expired"
            sub.is_active = False

            # Disable AI campaigns
            camp_stmt = (
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
            camp_result = await db.execute(camp_stmt)
            campaigns = camp_result.scalars().all()

            for campaign in campaigns:
                before_state = {
                    "ai_active": campaign.ai_active,
                }

                campaign.ai_active = False
                campaign.ai_deactivated_at = now

                after_state = {
                    "ai_active": campaign.ai_active,
                }

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

    # =====================================================
    # UI SUPPORT (READ-ONLY)
    # =====================================================
    @staticmethod
    async def get_ai_limit_status(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> dict:

        subscription = await PlanEnforcementService._get_active_subscription(
            db=db,
            user_id=user_id,
        )

        if not subscription:
            return {
                "allowed": False,
                "reason": "NO_SUBSCRIPTION",
            }

        override = await PlanEnforcementService._get_active_admin_override(
            db=db,
            user_id=user_id,
        )

        base_limit = subscription.ai_campaign_limit_snapshot or 0
        addon_extra = override.extra_ai_campaigns if override else 0
        effective_limit = base_limit + addon_extra

        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db=db,
            user_id=user_id,
        )

        return {
            "allowed": active_count < effective_limit,
            "active": active_count,
            "limit": effective_limit,
            "base_limit": base_limit,
            "addon_extra": addon_extra,
        }
