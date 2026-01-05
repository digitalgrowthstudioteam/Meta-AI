from datetime import date, datetime
from typing import List, Dict, Any
from uuid import UUID

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
    PHASE 8 — AUDIENCE / BREAKDOWN INSIGHTS (READ-ONLY)

    Ingests DAILY breakdown-level performance insights.

    LOCKED RULES:
    - ONLY selected ad account
    - READ-ONLY Meta
    - Stub-safe
    """

    # -----------------------------------------------------
    # PUBLIC ENTRY POINT
    # -----------------------------------------------------
    @staticmethod
    async def ingest_for_user(
        *,
        db: AsyncSession,
        user_id: UUID,
        since: date,
        until: date,
    ) -> int:
        """
        Fetches and stores DAILY breakdown metrics
        ONLY for the user's selected Meta ad account.
        """

        # 🔒 ONLY SELECTED AD ACCOUNT
        stmt = (
            select(MetaAdAccount)
            .join(
                UserMetaAdAccount,
                UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
            )
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
                MetaAdAccount.is_active.is_(True),
            )
        )

        result = await db.execute(stmt)
        ad_account: MetaAdAccount | None = result.scalar_one_or_none()

        if not ad_account:
            return 0

        rows_ingested = 0
        client = MetaCampaignInsightsClient(db)

        # -------------------------------------------------
        # CAMPAIGNS FOR SELECTED ACCOUNT
        # -------------------------------------------------
        stmt = (
            select(Campaign)
            .where(
                Campaign.ad_account_id == ad_account.id,
                Campaign.is_archived.is_(False),
            )
        )
        result = await db.execute(stmt)
        campaigns = result.scalars().all()

        if not campaigns:
            return 0

        campaign_map = {c.meta_campaign_id: c for c in campaigns}

        # -------------------------------------------------
        # BREAKDOWN SETS (LOCKED)
        # -------------------------------------------------
        breakdown_sets = [
            ["ad_id"],
            ["platform", "placement"],
            ["age", "gender"],
            ["region"],
        ]

        for breakdowns in breakdown_sets:
            try:
                insights: List[Dict[str, Any]] = (
                    await client.fetch_daily_insights_with_breakdown(
                        ad_account=ad_account,
                        since=since,
                        until=until,
                        breakdowns=breakdowns,
                    )
                )
            except Exception:
                continue

            if not insights:
                continue

            for row in insights:
                # -----------------------------
                # STUB / EMPTY → SKIP
                # -----------------------------
                if row.get("impressions", 0) == 0 and row.get("spend", 0) == 0:
                    continue

                campaign = campaign_map.get(row.get("campaign_meta_id"))
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
                    existing.meta_fetched_at = row.get(
                        "meta_fetched_at", datetime.utcnow()
                    )
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
                        meta_fetched_at=row.get(
                            "meta_fetched_at", datetime.utcnow()
                        ),
                    )
                    db.add(metric)

                rows_ingested += 1

        await db.commit()
        return rows_ingested
