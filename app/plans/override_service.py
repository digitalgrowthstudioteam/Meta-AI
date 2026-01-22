from datetime import datetime
from typing import Optional, Dict

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as UUIDType, uuid4

from app.plans.override_models import UserUsageOverride
from app.admin.models import AdminAuditLog


class UsageOverrideService:
    """
    Phase-10: Enterprise usage override resolution.
    Resolves: effective_limit = override ?? snapshot
    Upsert + Delete with audit.
    """

    # =========================
    # KEYS SUPPORTED
    # =========================
    VALID_KEYS = {
        "campaigns",
        "ad_accounts",
        "team_members",
        "credits",
    }

    # =========================
    # FETCH SINGLE OVERRIDE
    # =========================
    @staticmethod
    async def get_override(
        db: AsyncSession,
        *,
        user_id: UUIDType,
        key: str,
    ) -> Optional[UserUsageOverride]:
        if key not in UsageOverrideService.VALID_KEYS:
            raise ValueError(f"Invalid override key: {key}")

        result = await db.execute(
            select(UserUsageOverride).where(
                UserUsageOverride.user_id == user_id,
                UserUsageOverride.key == key,
                (
                    (UserUsageOverride.expires_at.is_(None))
                    | (UserUsageOverride.expires_at > datetime.utcnow())
                ),
            )
        )
        return result.scalar_one_or_none()

    # =========================
    # FETCH ALL OVERRIDES
    # =========================
    @staticmethod
    async def get_overrides_for_user(
        db: AsyncSession,
        *,
        user_id: UUIDType,
    ) -> Dict[str, dict]:
        result = await db.execute(
            select(UserUsageOverride).where(UserUsageOverride.user_id == user_id)
        )
        rows = result.scalars().all()

        response = {}
        for row in rows:
            response[row.key] = {
                "value": row.value,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "updated_by": str(row.updated_by) if row.updated_by else None,
            }

        return response

    # =========================
    # EFFECTIVE LIMIT RESOLUTION
    # =========================
    @staticmethod
    async def resolve_effective_limit(
        db: AsyncSession,
        *,
        user_id: UUIDType,
        key: str,
        snapshot_value: int,
    ) -> int:
        override = await UsageOverrideService.get_override(
            db=db,
            user_id=user_id,
            key=key,
        )
        if override:
            return override.value
        return snapshot_value

    # =========================
    # UPSERT OVERRIDE
    # =========================
    @staticmethod
    async def upsert_override(
        db: AsyncSession,
        *,
        admin_user_id: UUIDType,
        user_id: UUIDType,
        key: str,
        value: int,
        expires_at: datetime | None,
        reason: str,
    ) -> UserUsageOverride:
        if key not in UsageOverrideService.VALID_KEYS:
            raise ValueError(f"Invalid override key: {key}")

        existing = await UsageOverrideService.get_override(
            db=db,
            user_id=user_id,
            key=key,
        )

        before = {
            "value": existing.value if existing else None,
            "expires_at": existing.expires_at if existing else None,
        }

        if existing:
            existing.value = value
            existing.expires_at = expires_at
            existing.updated_by = admin_user_id
            override = existing
        else:
            override = UserUsageOverride(
                id=uuid4(),
                user_id=user_id,
                key=key,
                value=value,
                expires_at=expires_at,
                updated_by=admin_user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(override)

        after = {
            "value": override.value,
            "expires_at": override.expires_at,
        }

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="usage_override",
            target_id=override.id,
            action="override_upsert",
            before_state=before,
            after_state=after,
            reason=reason,
            rollback_token=None,
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        await db.commit()
        await db.refresh(override)
        return override

    # =========================
    # RESET OVERRIDE
    # =========================
    @staticmethod
    async def delete_override(
        db: AsyncSession,
        *,
        admin_user_id: UUIDType,
        user_id: UUIDType,
        key: str,
        reason: str,
    ) -> None:
        if key not in UsageOverrideService.VALID_KEYS:
            raise ValueError(f"Invalid override key: {key}")

        existing = await UsageOverrideService.get_override(
            db=db,
            user_id=user_id,
            key=key,
        )

        if not existing:
            return  # no-op

        before = {
            "value": existing.value,
            "expires_at": existing.expires_at,
        }

        await db.execute(
            delete(UserUsageOverride).where(
                UserUsageOverride.id == existing.id
            )
        )

        audit = AdminAuditLog(
            admin_user_id=admin_user_id,
            target_type="usage_override",
            target_id=existing.id,
            action="override_delete",
            before_state=before,
            after_state={},
            reason=reason,
            rollback_token=None,
            created_at=datetime.utcnow(),
        )

        db.add(audit)
        await db.commit()
