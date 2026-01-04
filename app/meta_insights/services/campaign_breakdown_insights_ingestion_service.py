from datetime import date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.meta_insights.clients.meta_campaign_insights_client import (
    MetaCampaignInsightsClient,
)
from app.meta_insights.models.campaign_breakdown_daily_metrics import (
    CampaignBreakdownDailyMetrics,
)


class CampaignBreakdownInsightsIngestionService:
    """
    Ingests DAILY breakdown-level performance insights from Meta.

    Breakdown types ingested separately:
    - Creative (ad_id)
    - Placement (platform, placement)
    - Demographics (age, gender)
    - Geo (region)

    Guarantees:
    - Read-only Meta access
    - Idempotent per (campaign, date, breakdown)
    - Safe for cron / batch execution
    - No AI / ML / aggregation logic
    """

    # -----------------------------------------------------
    # PUBLIC ENTRY POINT
    # -----------------------------------------------------
    @staticmethod
    async def ingest_for_user(
        *,
        db: AsyncSession,
        user_id,
        since: date,
        until: date,
    ) -> int:
        """
        Fetches and stores DAILY breakdown metrics
        for all active Meta ad accounts of a user.
        """

        # 1️⃣ Fetch active ad accounts
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

        # 2️⃣ Process each ad account independently
        for ad_account in ad_accounts:
            # Fetch campaigns for ID mapping
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

            # -----------------------------------------
            # 3️⃣ Run separate breakdown fetches
            # -----------------------------------------
            breakdown_sets = [
                ["ad_id"],                     # Creative
                ["platform", "placement"],     # Placement
                ["age", "gender"],             # Demographics
                ["region"],                    # Geo
            ]

            for breakdowns in breakdown_sets:
                insights = await MetaCampaignInsightsClient.fetch_daily_insights_with_breakdown(
                    ad_account=ad_account,
                    since=since,
                    until=until,
                    breakdowns=breakdowns,
                )

                if not insights:
                    continue

                for row in insights:
                    campaign = campaign_map.get(row["campaign_meta_id"])
                    if not campaign:
                        continue

                    stmt = (
                        select(CampaignBreakdownDailyMetrics)
                        .where(
                            CampaignBreakdownDailyMetrics.campaign_id == campaign.id,
                            CampaignBreakdownDailyMetrics.metric_date == row["metric_date"],
                            CampaignBreakdownDailyMetrics.ad_id == row.get("ad_id"),
                            CampaignBreakdownDailyMetrics.platform == row.get("platform"),
                            CampaignBreakdownDailyMetrics.placement == row.get("placement"),
                            CampaignBreakdownDailyMetrics.age_group == row.get("age"),
                            CampaignBreakdownDailyMetrics.gender == row.get("gender"),
                            CampaignBreakdownDailyMetrics.region == row.get("region"),
                        )
                    )

                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
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
                        metric = CampaignBreakdownDailyMetrics(
                            campaign_id=campaign.id,
                            metric_date=row["metric_date"],
                            ad_id=row.get("ad_id"),
                            platform=row.get("platform"),
                            placement=row.get("placement"),
                            age_group=row.get("age"),
                            gender=row.get("gender"),
                            region=row.get("region"),
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
