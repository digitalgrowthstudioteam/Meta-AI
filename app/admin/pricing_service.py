from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.admin.models import AdminAuditLog
from app.admin.models_pricing import AdminPricingConfig


class AdminPricingConfigService:
    """
    Admin-only pricing configuration service.
    - Versioned
    - Single active config enforced
    - Fully audited
    """

    # =====================================================
    # READ — ACTIVE CONFIG
    # =====================================================
    @staticmethod
    async def get_active_config(db: AsyncSession) -> AdminPricingConfig | None:
        return await db.scalar(
            select(AdminPricingConfig)
            .where(AdminPricingConfig.is_active.is_(True))
            .limit(1)
        )

    # =====================================================
    # READ — ALL VERSIONS
    # =====================================================
    @staticmethod
    async def list_configs(db: AsyncSession) -> list[AdminPricingConfig]:
        result = await db.execute(
            select(AdminPricingConfig)
            .order_by(AdminPricingConfig.version.desc())
        )
        return result.scalars().all()

    # =====================================================
    # CREATE — NEW VERSION (INACTIVE)
    # =====================================================
    @staticmethod
    async def create_config(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        plan_pricing: dict,
        slot_packs: dict,
        currency: str,
        tax_percentage: int,
        invoice_prefix: str,
        invoice_notes: str | None,
        razorpay_mode: str,
        reason: str,
    ) -> AdminPricingConfig:
        last_version = await db.scalar(
            select(func.max(AdminPricingConfig.version))
        )
        next_version = (last_version or 0) + 1

        config = AdminPricingConfig(
            version=next_version,
            is_active=False,
            plan_pricing=plan_pricing,
            slot_packs=slot_packs,
            currency=currency,
            tax_percentage=tax_percentage,
            invoice_prefix=invoice_prefix,
            invoice_notes=invoice_notes,
            razorpay_mode=razorpay_mode,
            created_by_admin_id=admin_user_id,
            created_at=datetime.utcnow(),
        )

        db.add(config)

        db.add(
            AdminAuditLog(
                admin_user_id=admin_user_id,
                target_type="pricing_config",
                target_id=config.id,
                action="create_pricing_config",
                before_state={},
                after_state={
                    "version": next_version,
                    "currency": currency,
                    "tax_percentage": tax_percentage,
                    "razorpay_mode": razorpay_mode,
                },
                reason=reason,
                created_at=datetime.utcnow(),
            )
        )

        await db.commit()
        await db.refresh(config)
        return config

    # =====================================================
    # ACTIVATE — VERSION SWITCH (ATOMIC)
    # =====================================================
    @staticmethod
    async def activate_config(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        config_id: UUID,
        reason: str,
    ) -> None:
        active_config = await AdminPricingConfigService.get_active_config(db)
        target = await db.get(AdminPricingConfig, config_id)

        if not target:
            raise ValueError("Pricing config not found")

        before_state = (
            {"active_version": active_config.version}
            if active_config
            else {}
        )

        # deactivate current
        await db.execute(
            update(AdminPricingConfig)
            .where(AdminPricingConfig.is_active.is_(True))
            .values(is_active=False)
        )

        # activate target
        target.is_active = True
        target.activated_at = datetime.utcnow()

        after_state = {"active_version": target.version}

        db.add(
            AdminAuditLog(
                admin_user_id=admin_user_id,
                target_type="pricing_config",
                target_id=target.id,
                action="activate_pricing_config",
                before_state=before_state,
                after_state=after_state,
                reason=reason,
                created_at=datetime.utcnow(),
            )
        )

        await db.commit()
