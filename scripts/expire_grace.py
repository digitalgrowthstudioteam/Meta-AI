#!/usr/bin/env python3
"""
Auto-expire grace subscriptions.

Logic:
 - status = 'grace'
 - grace_ends_at < now()
 => status='expired', is_active=False
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, update
from app.core.db_session import AsyncSessionLocal
from app.plans.subscription_models import Subscription


async def expire_grace_subscriptions():
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        # find grace subs that passed grace window
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
