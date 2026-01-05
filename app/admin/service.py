from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.admin.models import AdminOverride
from app.campaigns.models import Campaign, CampaignActionLog


class AdminOverrideService:
    """
    Admin override business logic.

    🔒 RULES:
    - Overrides are additive
    - Overrides are time-bound
    - Overrides never mutate plans or subscriptions
    """

    # =====================================================
    # ADMIN OVERRIDES
    # =====================================================
    @staticmethod
    async def create_override(
        db: AsyncSession,
        *,
        user_id: UUID,
        extra_ai_campaigns: int,
        force_ai_enabled: bool,
        override_expires_at,
        reason: str | None,
    ) -> AdminOverride:
        override = AdminOverride(
            user_id=user_id,
            extra_ai_campaigns=extra_ai_campaigns,
            force_ai_enabled=force_ai_enabled,
            override_expires_at=override_expires_at,
            reason=reason,
        )

        db.add(override)
        await db.commit()
        await db.refresh(override)

        return override

    @staticmethod
    async def list_overrides(
        db: AsyncSession,
    ) -> list[AdminOverride]:
        stmt = select(AdminOverride)
        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # PHASE 10.3 — ROLLBACK ENGINE (ADMIN / SYSTEM ONLY)
    # =====================================================
    @staticmethod
    async def rollback_campaign_action(
        db: AsyncSession,
        *,
        action_log_id: UUID,
        admin_user_id: UUID,
        reason: str,
    ) -> Campaign:
        """
        Rollback a campaign to BEFORE state from action log.
        - Immutable audit
        - Admin-only
        """

        # 🔒 Lock action log
        stmt = (
            select(CampaignActionLog)
            .where(CampaignActionLog.id == action_log_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            raise ValueError("Action log not found")

        # 🔒 Lock campaign
        stmt = (
            select(Campaign)
            .where(Campaign.id == log.campaign_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        # Snapshot BEFORE rollback (current state)
        rollback_before = {
            "ai_active": campaign.ai_active,
            "ai_activated_at": campaign.ai_activated_at.isoformat() if campaign.ai_activated_at else None,
            "ai_deactivated_at": campaign.ai_deactivated_at.isoformat() if campaign.ai_deactivated_at else None,
        }

        # Restore from log.before_state
        campaign.ai_active = log.before_state.get("ai_active", campaign.ai_active)
        campaign.ai_activated_at = (
            datetime.fromisoformat(log.before_state["ai_activated_at"])
            if log.before_state.get("ai_activated_at")
            else None
        )
        campaign.ai_deactivated_at = (
            datetime.fromisoformat(log.before_state["ai_deactivated_at"])
            if log.before_state.get("ai_deactivated_at")
            else None
        )

        # Snapshot AFTER rollback
        rollback_after = {
            "ai_active": campaign.ai_active,
            "ai_activated_at": campaign.ai_activated_at.isoformat() if campaign.ai_activated_at else None,
            "ai_deactivated_at": campaign.ai_deactivated_at.isoformat() if campaign.ai_deactivated_at else None,
        }

        # 🔒 Log rollback action (immutable)
        db.add(
            CampaignActionLog(
                campaign_id=campaign.id,
                user_id=admin_user_id,
                actor_type="admin",
                action_type="rollback",
                before_state=rollback_before,
                after_state=rollback_after,
                reason=reason,
            )
        )

        await db.commit()
        await db.refresh(campaign)
        return campaign
