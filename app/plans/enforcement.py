from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import select
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
    🔒 SINGLE SOURCE OF TRUTH FOR LIMITS
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
        """
        Count ONLY campaigns belonging to the user
        across their selected ad accounts.
        """

        stmt = (
            select(Campaign)
            .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                Campaign.ai_active.is_(True),
                Campaign.is_archived.is_(False),
            )
        )

        result = await db.execute(stmt)
        return len(result.scalars().all())

    # =====================================================
    # PUBLIC GATE
    # =====================================================
    @staticmethod
    async def can_activate_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        """
        Hard enforcement gate for AI activation.
        """

        subscription = await PlanEnforcementService._get_active_subscription(
            db, user_id
        )

        if not subscription:
            raise EnforcementError(
                code="NO_SUBSCRIPTION",
                message="No active trial or subscription found.",
                action="UPGRADE_PLAN",
            )

        now = datetime.utcnow()

        if subscription.ends_at and now > subscription.ends_at:
            raise EnforcementError(
                code="SUBSCRIPTION_EXPIRED",
                message="Your trial or subscription has expired.",
                action="RENEW_PLAN",
            )

        base_limit = subscription.ai_campaign_limit_snapshot or 0

        override = await PlanEnforcementService._get_active_admin_override(
            db, user_id
        )

        extra = override.extra_ai_campaigns if override else 0
        effective_limit = base_limit + extra

        active_count = await PlanEnforcementService._count_active_ai_campaigns(
            db, user_id
        )

        if active_count >= effective_limit:
            raise EnforcementError(
                code="AI_LIMIT_REACHED",
                message=f"AI campaign limit reached ({effective_limit}).",
                action="UPGRADE_PLAN",
            )
