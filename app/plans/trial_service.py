from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.plans.subscription_models import Subscription
from app.plans.models import Plan


class TrialService:
    TRIAL_STATUS = "trial"

    @staticmethod
    async def ensure_trial(db: AsyncSession, user_id):
        # Check existing active/trial/grace subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace"]),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Load FREE plan
        plan = await db.scalar(
            select(Plan).where(
                Plan.name == "FREE",
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            return None

        # Determine trial period
        days = plan.trial_days or 7
        today = date.today()
        trial_end = today + timedelta(days=days)

        sub = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            status=TrialService.TRIAL_STATUS,
            billing_cycle="trial",
            is_trial=True,
            trial_start=today,
            trial_end=trial_end,
            starts_at=datetime.utcnow(),
            ends_at=None,
            is_active=True,
            ai_campaign_limit_snapshot=plan.max_ai_campaigns or 0,
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        return sub
