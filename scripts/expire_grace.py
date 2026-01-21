#!/usr/bin/env python3
"""
Auto-expire grace subscriptions

Handles naive + aware timestamps safely for PostgreSQL.
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.db_session import AsyncSessionLocal
from app.plans.subscription_models import Subscription


def to_utc_naive(dt):
    """
    Convert timezone-aware → UTC naive
    Convert naive → return as-is
    """
    if dt is None:
        return None
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def expire_grace_subscriptions():
    # (A) normalize now to UTC naive
    now = to_utc_naive(datetime.now(timezone.utc))

    async with AsyncSessionLocal() as db:
        # (B) load all grace subs first (safer than direct timestamp filter)
        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == "grace")
            .where(Subscription.grace_ends_at.is_not(None))
        )
        subs = result.scalars().all()

        if not subs:
            print("[GRACE-CHECK] no grace subscriptions found")
            return

        expired = 0

        for sub in subs:
            sub_end = to_utc_naive(sub.grace_ends_at)
            if sub_end and sub_end < now:
                sub.status = "expired"
                sub.is_active = False
                expired += 1

        if expired > 0:
            await db.commit()

        print(f"[GRACE-CHECK] expired={expired}, checked={len(subs)}")


if __name__ == "__main__":
    asyncio.run(expire_grace_subscriptions())
