"""
Background job: Sync Meta campaigns for all users.

SAFE TO RUN:
- systemd timer
- manual CLI
- repeated executions (idempotent)

Golden Rules:
- Uses canonical async DB session
- No direct engine usage
- No business logic duplication
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import async_session
from app.users.models import User
from app.meta.models import UserMetaAdAccount
from app.campaigns.service import CampaignService


# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [campaign-sync] %(levelname)s: %(message)s",
)
logger = logging.getLogger("campaign-sync")


# =========================================================
# CORE JOB
# =========================================================
async def sync_all_users_campaigns() -> None:
    """
    Sync campaigns for all users
    who have at least one Meta ad account connected.
    """

    async with async_session() as db:  # type: AsyncSession
        # -------------------------------------------------
        # 1️⃣ Fetch users with Meta access
        # -------------------------------------------------
        stmt = (
            select(User.id)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.user_id == User.id,
            )
            .distinct()
        )

        result = await db.execute(stmt)
        user_ids: list[UUID] = result.scalars().all()

        if not user_ids:
            logger.info("No users with Meta ad accounts found")
            return

        logger.info("Starting campaign sync for %d users", len(user_ids))

        # -------------------------------------------------
        # 2️⃣ Sync campaigns per user (isolated failures)
        # -------------------------------------------------
        for user_id in user_ids:
            try:
                campaigns = await CampaignService.sync_from_meta(
                    db=db,
                    user_id=user_id,
                )
                logger.info(
                    "User %s: synced %d campaigns",
                    user_id,
                    len(campaigns),
                )
            except Exception as exc:
                logger.error(
                    "User %s: campaign sync failed → %s",
                    user_id,
                    str(exc),
                )

        logger.info("Campaign sync job completed")


# =========================================================
# ENTRYPOINT
# =========================================================
def main() -> None:
    asyncio.run(sync_all_users_campaigns())


if __name__ == "__main__":
    main()
