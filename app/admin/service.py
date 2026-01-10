from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from uuid import UUID, uuid4
from datetime import datetime

from app.admin.models import (
    AdminOverride,
    GlobalSettings,
    AdminAuditLog,
)
from app.campaigns.models import Campaign
from app.users.models import User
from app.plans.subscription_models import Subscription


class AdminOverrideService:
    """
    Admin override & control business logic.
    All admin mutations MUST be audited here.
    """

    # =====================================================
    # ADMIN DASHBOARD STATS (READ-ONLY)
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

        last_audit = await db.scalar(
            select(AdminAuditLog.created_at)
            .order_by(AdminAuditLog.created_at.desc())
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
                last_audit.isoformat() if last_audit else None
            ),
            "system_status": "ok",
        }

    # =====================================================
    # GLOBAL SETTINGS (AUDITED + ROLLBACK SAFE)
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
        ip_address: str | None = None,
        user_agent: str | None = None,
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

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="system",
            target_id=settings.id,
            action="global_settings_update",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            rollback_token=uuid4(),
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        await db.commit()
        await db.refresh(settings)
        return settings

    # =====================================================
    # PHASE 8.3 — RISK ACTIONS (USER LEVEL)
    # =====================================================
    @staticmethod
    async def freeze_user(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        target_user_id: UUID,
        reason: str,
    ) -> None:
        user = await db.scalar(select(User).where(User.id == target_user_id))
        if not user:
            raise ValueError("User not found")

        before_state = {"is_active": user.is_active}

        await db.execute(
            update(User)
            .where(User.id == target_user_id)
            .values(is_active=False)
        )

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="user",
            target_id=target_user_id,
            action="risk_freeze_user",
            before_state=before_state,
            after_state={"is_active": False},
            reason=reason,
            rollback_token=uuid4(),
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        await db.commit()

    @staticmethod
    async def unfreeze_user(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        target_user_id: UUID,
        reason: str,
    ) -> None:
        user = await db.scalar(select(User).where(User.id == target_user_id))
        if not user:
            raise ValueError("User not found")

        before_state = {"is_active": user.is_active}

        await db.execute(
            update(User)
            .where(User.id == target_user_id)
            .values(is_active=True)
        )

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="user",
            target_id=target_user_id,
            action="risk_unfreeze_user",
            before_state=before_state,
            after_state={"is_active": True},
            reason=reason,
            rollback_token=uuid4(),
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        await db.commit()

    @staticmethod
    async def disable_user_ai(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        target_user_id: UUID,
        reason: str,
    ) -> None:
        override = AdminOverride(
            user_id=target_user_id,
            force_ai_enabled=False,
            reason=reason,
            created_at=datetime.utcnow(),
        )

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="user",
            target_id=target_user_id,
            action="risk_disable_user_ai",
            before_state={},
            after_state={"force_ai_enabled": False},
            reason=reason,
            rollback_token=uuid4(),
            created_at=datetime.utcnow(),
        )

        db.add_all([override, audit])
        await db.commit()

    # =====================================================
    # PHASE 6.4 — ROLLBACK ENGINE (ADMIN ONLY)
    # =====================================================
    @staticmethod
    async def rollback_by_token(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        rollback_token: UUID,
        reason: str,
    ) -> None:
        audit = await db.scalar(
            select(AdminAuditLog)
            .where(AdminAuditLog.rollback_token == rollback_token)
        )

        if not audit:
            raise ValueError("Invalid rollback token")

        if audit.target_type != "system":
            raise ValueError("Rollback not supported for this target")

        settings = await AdminOverrideService.get_global_settings(db)

        for field, value in audit.before_state.items():
            if hasattr(settings, field):
                setattr(settings, field, value)

        rollback_audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="system",
            target_id=settings.id,
            action="rollback_global_settings",
            before_state=audit.after_state,
            after_state=audit.before_state,
            reason=reason,
            rollback_token=None,
            created_at=datetime.utcnow(),
        )

        db.add(rollback_audit)
        await db.commit()
