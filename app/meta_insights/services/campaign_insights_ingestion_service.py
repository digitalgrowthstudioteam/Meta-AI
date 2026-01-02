from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import List

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics
from app.meta_insights.clients.meta_campaign_insights_client import (
    MetaCampaignInsightsClient,
)


class CampaignInsightsIngestionService:
    """
    Ingests DAILY campaign-level performance insights from Meta
    into campaign_daily_metrics.

    Design guarantees:
    - Read-only Meta access
    - Account timezone aware
    - Idempotent per (campaign_id, metric_date)
    - Zero rows are stored explicitly
    - No AI logic
    - Safe for cron / batch jobs
    """

    @staticmethod
    async def ingest_for_user(
        *,
        db: AsyncSession,
        user_id,
        since: date,
        until: date,
    ) -> int:
        """
        Fetches and stores campaign daily metrics for all
        Meta ad accounts the user has access to.

        Returns number of metric rows ingested.
        """

        # =================================================
        # 1️⃣ Fetch active Meta ad accounts for user
        # =================================================
        stmt = (
            select(MetaAdAccount)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                MetaAdAccount.is_active.is_(True),
            )
        )

        result = await db.execute(stmt)
        ad_accounts: List[MetaAdAccount] = result.scalars().all()

        if not ad_accounts:
            return 0

        rows_ingested = 0

        # =================================================
        # 2️⃣ Process each ad account independently
        # =================================================
        for ad_account in ad_accounts:
            insights = await MetaCampaignInsightsClient.fetch_daily_insights(
                ad_account=ad_account,
                since=since,
                until=until,
            )

            if not insights:
                continue

            # Fetch campaigns for mapping
            stmt = (
                select(Campaign)
                .where(
                    Campaign.ad_account_id == ad_account.id,
                    Campaign.is_archived.is_(False),
                )
            )

            result = await db.execute(stmt)
            campaigns = result.scalars().all()

            campaign_map = {
                c.meta_campaign_id: c for c in campaigns
            }

            # =================================================
            # 3️⃣ Upsert daily metrics (IDEMPOTENT)
            # =================================================
            for row in insights:
                campaign = campaign_map.get(row["campaign_meta_id"])
                if not campaign:
                    continue

                stmt = (
                    select(CampaignDailyMetrics)
                    .where(
                        CampaignDailyMetrics.campaign_id == campaign.id,
                        CampaignDailyMetrics.metric_date == row["metric_date"],
                    )
                )

                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update snapshot safely
                    existing.impressions = row["impressions"]
                    existing.clicks = row["clicks"]
                    existing.spend = row["spend"]
                    existing.conversions = row["conversions"]
                    existing.conversion_value = row["conversion_value"]
                    existing.ctr = row["ctr"]
                    existing.cpl = row["cpl"]
                    existing.cpa = row["cpa"]
                    existing.roas = row["roas"]
                    existing.meta_fetched_at = row["meta_fetched_at"]
                else:
                    metric = CampaignDailyMetrics(
                        campaign_id=campaign.id,
                        metric_date=row["metric_date"],
                        impressions=row["impressions"],
                        clicks=row["clicks"],
                        spend=row["spend"],
                        conversions=row["conversions"],
                        conversion_value=row["conversion_value"],
                        ctr=row["ctr"],
                        cpl=row["cpl"],
                        cpa=row["cpa"],
                        roas=row["roas"],
                        objective_type=campaign.objective,
                        meta_account_id=ad_account.meta_account_id,
                        meta_fetched_at=row["meta_fetched_at"],
                    )
                    db.add(metric)

                rows_ingested += 1

        await db.commit()
        return rows_ingested
