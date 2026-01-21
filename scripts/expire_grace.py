#!/usr/bin/env python3
"""
Auto-expire grace subscriptions.

Fix: convert timezone-aware UTC -> naive UTC for PG.
"""

import asyncio
from datetime import datetime

from sqlalchemy import select
from app.core.db_session import AsyncSessionLocal
from app.plans.subscription_models import Subscription


async def expire_grace_subscriptions():
    # PG stores timestamps as naive UTC → use naive datetime.utcnow()
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        stmt = (
            select(Subscription)
            .where(Subscription.status == "grace")
            .where(Subscription.grace_ends_at.is_not(None))
            .where(Subscription.grace_ends_at < now)
        )

        result = await db.execute(stmt)
        subs = result.scalars().all()

        if not subs:
            print("[GRACE-CHECK] no expired grace subscriptions found")
            return

        for sub in subs:
            sub.status = "expired"
            sub.is_active = False

        await db.commit()
        print(f"[GRACE-CHECK] expired {len(subs)} subscriptions")


if __name__ == "__main__":
    asyncio.run(expire_grace_subscriptions())
