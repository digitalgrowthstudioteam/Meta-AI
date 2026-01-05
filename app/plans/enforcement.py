from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.subscription_models import Subscription
from app.admin.models import AdminOverride
from app.campaigns.models import Campaign
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
    🔒 SINGLE SOURCE OF TRUTH FOR PLAN + ADD-ON ENFORCEMENT
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
    # PUBLIC ENFORCEMENT GATES
    # =====================================================
    @staticmethod
    async def assert_ai_allowed(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        """
        Master gate.
        Used before ANY AI activation.
        """

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
            # Distinguish plan vs add-on overflow
            if addon_extra > 0:
                raise EnforcementError(
                    code="AI_ADDON_LIMIT_REACHED",
                    message=(
                        f"AI add-on limit reached "
                        f"({effective_limit})."
                    ),
                    action="BUY_ADDON",
                )

            raise EnforcementError(
                code="AI_PLAN_LIMIT_REACHED",
                message=(
                    f"AI campaign limit reached "
                    f"({effective_limit})."
                ),
                action="UPGRADE_PLAN",
            )

    # =====================================================
    # UI SUPPORT (READ-ONLY)
    # =====================================================
    @staticmethod
    async def get_ai_limit_status(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> dict:
        """
        UI helper:
        Returns limits + reason for lock.
        """

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
