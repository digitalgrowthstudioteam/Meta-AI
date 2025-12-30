from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.admin.models import AdminOverride


class AdminOverrideService:
    """
    Admin override business logic.

    🔒 RULES:
    - Overrides are additive
    - Overrides are time-bound
    - Overrides never mutate plans or subscriptions
    """

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
