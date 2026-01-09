from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, date

from app.admin.models import AdminOverride, GlobalSettings
from app.campaigns.models import Campaign, CampaignActionLog
from app.chat.models import ChatThread, ChatMessage
from app.users.models import User
from app.plans.subscription_models import Subscription


class AdminOverrideService:
    """
    Admin override & control business logic.
    READ-ONLY metrics for dashboard.
    """

    # =====================================================
    # ADMIN DASHBOARD STATS (PHASE 2.1 — NORMALIZED)
    # =====================================================
    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> dict:
        users_total = await db.scalar(select(func.count(User.id)))

        subs_active = await db.scalar(
            select(func.count(Subscription.id))
            .where(Subscription.status == "active")
        )
        subs_expired = await db.scalar(
            select(func.count(Subscription.id))
            .where(Subscription.status == "expired")
        )

        campaigns_total = await db.scalar(select(func.count(Campaign.id)))
        campaigns_ai_active = await db.scalar(
            select(func.count(Campaign.id))
            .where(Campaign.ai_active.is_(True))
        )
        campaigns_manual = await db.scalar(
            select(func.count(Campaign.id))
            .where(Campaign.is_manual.is_(True))
        )

        last_activity = await db.scalar(
            select(CampaignActionLog.created_at)
            .order_by(CampaignActionLog.created_at.desc())
            .limit(1)
        )

        return {
            "users": users_total or 0,
            "subscriptions": {
                "active": subs_active or 0,
                "expired": subs_expired or 0,
            },
            "campaigns": {
                "total": campaigns_total or 0,
                "ai_active": campaigns_ai_active or 0,
                "manual": campaigns_manual or 0,
            },
            "last_activity": (
                last_activity.isoformat() if last_activity else None
            ),
            "system_status": "ok",
        }

    # =====================================================
    # GLOBAL SETTINGS (UNCHANGED)
    # =====================================================
    @staticmethod
    async def get_global_settings(db: AsyncSession) -> GlobalSettings:
        result = await db.execute(select(GlobalSettings).limit(1))
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
