from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminAuditLog
from app.users.models import User

from app.plans.subscription_models import Subscription  # for future use
from app.plans.override_models import UserUsageOverride


VALID_KEYS = {"campaigns", "ad_accounts", "team_members", "credits"}


class UsageOverrideService:
    """
    Manual admin usage override system.

    Priority:
        effective_limit = override.value (if exists & not expired) else plan_default

    UsageOverride stored per (user_id, key)
    """

    # =====================================================
    # GET OVERRIDES FOR USER
    # =====================================================
    @staticmethod
    async def get_overrides_for_user(
        *,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[UserUsageOverride]:
        now = datetime.utcnow()
        stmt = (
            select(UserUsageOverride)
            .where(
                UserUsageOverride.user_id == user_id,
                (
                    (UserUsageOverride.expires_at.is_(None)) |
                    (UserUsageOverride.expires_at > now)
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # UPSERT OVERRIDE (INSERT OR UPDATE)
    # =====================================================
    @staticmethod
    async def upsert_override(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        user_id: UUID,
        key: str,
        value: int,
        expires_at: datetime | None,
        reason: str,
    ) -> UserUsageOverride:
        if key not in VALID_KEYS:
            raise ValueError(f"Invalid override key '{key}'")

        now = datetime.utcnow()

        # Check if exists
        stmt = (
            select(UserUsageOverride)
            .where(
                UserUsageOverride.user_id == user_id,
                UserUsageOverride.key == key,
            )
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.value = value
            existing.expires_at = expires_at
            existing.updated_by = admin_user_id
            existing.updated_at = now

            # AUDIT LOG
            audit = AdminAuditLog(
                admin_user_id=admin_user_id,
                target_type="user",
                target_id=user_id,
                action="usage_override_update",
                before_state={"value": existing.value},
                after_state={"value": value},
                reason=reason,
                rollback_token=None,
                created_at=now,
            )
            db.add(audit)

            await db.commit()
            await db.refresh(existing)
            return existing

        # Create new override
        override = UserUsageOverride(
            user_id=user_id,
            key=key,
            value=value,
            expires_at=expires_at,
            updated_by=admin_user_id,
            updated_at=now,
        )
        db.add(override)

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="user",
            target_id=user_id,
            action="usage_override_create",
            before_state={},
            after_state={"value": value},
            reason=reason,
            rollback_token=None,
            created_at=now,
        )
        db.add(audit)

        await db.commit()
        await db.refresh(override)
        return override

    # =====================================================
    # DELETE OVERRIDE (RESET TO PLAN DEFAULT)
    # =====================================================
    @staticmethod
    async def delete_override(
        *,
        db: AsyncSession,
        admin_user_id: UUID,
        user_id: UUID,
        key: str,
        reason: str,
    ) -> None:
        stmt = (
            select(UserUsageOverride)
            .where(
                UserUsageOverride.user_id == user_id,
                UserUsageOverride.key == key,
            )
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if not existing:
            return

        before_value = existing.value

        await db.execute(
            delete(UserUsageOverride)
            .where(
                UserUsageOverride.user_id == user_id,
                UserUsageOverride.key == key,
            )
        )

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="user",
            target_id=user_id,
            action="usage_override_delete",
            before_state={"value": before_value},
            after_state={},
            reason=reason,
            rollback_token=None,
            created_at=datetime.utcnow(),
        )
        db.add(audit)

        await db.commit()

    # =====================================================
    # EFFECTIVE LIMIT HELPERS (FOR ENFORCEMENT)
    # =====================================================
    @staticmethod
    async def get_effective_limit(
        *,
        db: AsyncSession,
        user_id: UUID,
        key: str,
        plan_default: int,
    ) -> int:
        """
        Returns override if valid, else plan default
        """
        if key not in VALID_KEYS:
            raise ValueError(f"Invalid override key '{key}'")

        now = datetime.utcnow()

        stmt = (
            select(UserUsageOverride.value)
            .where(
                UserUsageOverride.user_id == user_id,
                UserUsageOverride.key == key,
                (
                    (UserUsageOverride.expires_at.is_(None)) |
                    (UserUsageOverride.expires_at > now)
                )
            )
        )
        value = (await db.execute(stmt)).scalar_one_or_none()
        return value if value is not None else plan_default
