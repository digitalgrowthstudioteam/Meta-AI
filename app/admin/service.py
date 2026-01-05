from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, date

from app.admin.models import AdminOverride
from app.campaigns.models import Campaign, CampaignActionLog


class AdminOverrideService:
    """
    Admin override & control business logic.

    🔒 RULES:
    - Admin actions are authoritative
    - All actions are logged
    - No silent state mutation
    """

    # =====================================================
    # ADMIN OVERRIDES (PLAN / AI LIMIT)
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
    # PHASE 10.3 — ROLLBACK ENGINE
    # =====================================================
    @staticmethod
    async def rollback_campaign_action(
        db: AsyncSession,
        *,
        action_log_id: UUID,
        admin_user_id: UUID,
        reason: str,
    ) -> Campaign:

        stmt = (
            select(CampaignActionLog)
            .where(CampaignActionLog.id == action_log_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            raise ValueError("Action log not found")

        stmt = (
            select(Campaign)
            .where(Campaign.id == log.campaign_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        rollback_before = {
            "ai_active": campaign.ai_active,
            "ai_activated_at": campaign.ai_activated_at.isoformat() if campaign.ai_activated_at else None,
            "ai_deactivated_at": campaign.ai_deactivated_at.isoformat() if campaign.ai_deactivated_at else None,
        }

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

        rollback_after = {
            "ai_active": campaign.ai_active,
            "ai_activated_at": campaign.ai_activated_at.isoformat() if campaign.ai_activated_at else None,
            "ai_deactivated_at": campaign.ai_deactivated_at.isoformat() if campaign.ai_deactivated_at else None,
        }

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

    # =====================================================
    # PHASE 11.3 — MANUAL CAMPAIGN PURCHASE / RENEWAL
    # =====================================================
    @staticmethod
    async def grant_or_renew_manual_campaign(
        db: AsyncSession,
        *,
        campaign_id: UUID,
        admin_user_id: UUID,
        valid_from: date,
        valid_till: date,
        price_paid: float,
        plan_label: str,
        reason: str,
    ) -> Campaign:
        """
        Admin-only manual campaign purchase / renewal.
        """

        stmt = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Campaign not found")

        before_state = {
            "is_manual": campaign.is_manual,
            "manual_status": campaign.manual_status,
            "manual_valid_till": str(campaign.manual_valid_till) if campaign.manual_valid_till else None,
        }

        campaign.is_manual = True
        campaign.manual_purchased_at = datetime.utcnow()
        campaign.manual_valid_from = valid_from
        campaign.manual_valid_till = valid_till
        campaign.manual_price_paid = price_paid
        campaign.manual_purchase_plan = plan_label
        campaign.manual_status = "active"

        after_state = {
            "is_manual": campaign.is_manual,
            "manual_status": campaign.manual_status,
            "manual_valid_till": str(campaign.manual_valid_till),
        }

        db.add(
            CampaignActionLog(
                campaign_id=campaign.id,
                user_id=admin_user_id,
                actor_type="admin",
                action_type="manual_purchase",
                before_state=before_state,
                after_state=after_state,
                reason=reason,
            )
        )

        await db.commit()
        await db.refresh(campaign)
        return campaign
