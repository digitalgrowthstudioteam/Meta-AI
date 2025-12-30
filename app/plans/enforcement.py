from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.plans.subscription_models import Subscription
from app.admin.models import AdminOverride
from app.campaigns.models import Campaign


class EnforcementError(Exception):
    """Raised when an enforcement rule is violated."""


class PlanEnforcementService:
    """
    Central enforcement engine.

    🔒 RULES:
    - This is the ONLY place where limits are calculated
    - UI, API, AI must ALL obey this service
    """

    @staticmethod
    async def _get_active_subscription(
        db: AsyncSession,
        user_id: UUID,
    ) -> Subscription | None:
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
    ) -> AdminOverride | None:
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
        stmt = select(Campaign).where(
            Campaign.user_id == user_id,
            Campaign.ai_active.is_(True),
        )
        result = await db.execute(stmt)
        return len(result.scalars().all())

    # =========================================================
    # PUBLIC API
    # =========================================================

    @staticmethod
    async def can_activate_ai(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> None:
        """
        Raises EnforcementError if AI cannot be activated.
        """

        subscription = await PlanEnforcementService._get_active_subscription(
            db, user_id
        )

        if not subscription:
            raise EnforcementError("No active subscription or trial found")

        now = datetime.utcnow()

        # ⛔ Trial / subscription expired
        if subscription.ends_at and now > subscription.ends_at:
            raise EnforcementError("Your trial or subscription has expired")

        # Base limit (snapshot)
        base_limit = subscription.ai_campaign_limit_snapshot or 0

        # Admin override (if any)
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
                f"AI campaign limit reached ({effective_limit})"
            )
