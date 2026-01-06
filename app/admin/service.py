from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, date

from app.admin.models import AdminOverride, GlobalSettings
from app.campaigns.models import Campaign, CampaignActionLog
from app.users.models import User
from app.plans.subscription_models import Subscription


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
        result = await db.execute(select(AdminOverride))
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

        result = await db.execute(
            select(CampaignActionLog)
            .where(CampaignActionLog.id == action_log_id)
            .with_for_update()
        )
        log = result.scalar_one_or_none()
        if not log:
            raise ValueError("Action log not found")

        result = await db.execute(
            select(Campaign)
            .where(Campaign.id == log.campaign_id)
            .with_for_update()
        )
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

        result = await db.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .with_for_update()
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")

        before_state = {
            "is_manual": campaign.is_manual,
            "manual_valid_till": str(getattr(campaign, "manual_valid_till", None)),
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

    # =====================================================
    # PHASE 14.1 — ADMIN DASHBOARD STATS (READ-ONLY)
    # =====================================================
    @staticmethod
    async def get_dashboard_stats(
        db: AsyncSession,
    ) -> dict:

        total_users = await db.scalar(select(func.count(User.id)))
        active_subs = await db.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == "active")
        )
        expired_subs = await db.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == "expired")
        )
        total_campaigns = await db.scalar(select(func.count(Campaign.id)))
        ai_active_campaigns = await db.scalar(
            select(func.count(Campaign.id)).where(Campaign.ai_active.is_(True))
        )
        manual_campaigns = await db.scalar(
            select(func.count(Campaign.id)).where(Campaign.is_manual.is_(True))
        )

        last_log = await db.scalar(
            select(CampaignActionLog)
            .order_by(CampaignActionLog.created_at.desc())
            .limit(1)
        )

        return {
            "users_total": total_users,
            "subscriptions_active": active_subs,
            "subscriptions_expired": expired_subs,
            "campaigns_total": total_campaigns,
            "campaigns_ai_active": ai_active_campaigns,
            "campaigns_manual": manual_campaigns,
            "last_cron_run": last_log.created_at.isoformat() if last_log else None,
            "system_status": "ok",
        }

    # =====================================================
    # PHASE 14.4 — GLOBAL SETTINGS (SINGLETON)
    # =====================================================
    @staticmethod
    async def get_global_settings(
        db: AsyncSession,
    ) -> GlobalSettings:
        """
        Fetch global settings.
        Auto-creates singleton row if missing.
        """

        result = await db.execute(
            select(GlobalSettings).limit(1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = GlobalSettings()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        return settings

    @staticmethod
    async def update_global_settings(
        db: AsyncSession,
        *,
        admin_user_id: UUID,
        updates: dict,
        reason: str,
    ) -> GlobalSettings:
        """
        Admin-only global settings update (audited).
        """

        settings = await AdminOverrideService.get_global_settings(db)

        before_state = {
            "site_name": settings.site_name,
            "dashboard_title": settings.dashboard_title,
            "logo_url": settings.logo_url,
            "ai_globally_enabled": settings.ai_globally_enabled,
            "meta_sync_enabled": settings.meta_sync_enabled,
            "maintenance_mode": settings.maintenance_mode,
        }

        for field, value in updates.items():
            if hasattr(settings, field):
                setattr(settings, field, value)

        after_state = {
            "site_name": settings.site_name,
            "dashboard_title": settings.dashboard_title,
            "logo_url": settings.logo_url,
            "ai_globally_enabled": settings.ai_globally_enabled,
            "meta_sync_enabled": settings.meta_sync_enabled,
            "maintenance_mode": settings.maintenance_mode,
        }

        db.add(
            CampaignActionLog(
                campaign_id=None,
                user_id=admin_user_id,
                actor_type="admin",
                action_type="global_settings_update",
                before_state=before_state,
                after_state=after_state,
                reason=reason,
            )
        )

        await db.commit()
        await db.refresh(settings)
        return settings
