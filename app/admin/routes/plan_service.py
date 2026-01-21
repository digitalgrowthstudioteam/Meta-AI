from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.plans.models import Plan


class PlanService:

    @staticmethod
    async def list_plans(db: AsyncSession):
        result = await db.execute(select(Plan).order_by(Plan.id.asc()))
        return result.scalars().all()

    @staticmethod
    async def update_plan(db: AsyncSession, plan_id: int, payload: dict):
        # Only allow specific editable fields
        allowed_fields = {
            "monthly_price",
            "yearly_price",
            "max_ad_accounts",
            "max_ai_campaigns",
            "is_active",
            "is_hidden",
            "auto_allowed",
            "manual_allowed",
            "yearly_allowed",
        }

        update_payload = {k: v for k, v in payload.items() if k in allowed_fields}

        if not update_payload:
            return

        await db.execute(
            update(Plan)
            .where(Plan.id == plan_id)
            .values(**update_payload)
        )

        await db.commit()
