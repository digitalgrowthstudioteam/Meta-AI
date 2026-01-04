from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.ai_engine.models.campaign_category_map import (
    CampaignCategoryMap,
    CategorySource,
)
from app.ai_engine.services.category_inference_service import (
    CategoryInferenceService,
)


class CategoryResolutionService:
    """
    Resolves campaign business category using ML inference + governance rules.

    This service:
    - ALWAYS runs inference
    - ONLY persists high-confidence decisions
    - NEVER overrides user-provided categories
    - Is safe to run as a scheduled background job
    """

    MIN_CONFIDENCE = 0.70
    INFERENCE_VERSION = "v1.0"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.inference_service = CategoryInferenceService()

    # --------------------------------------------------
    # ENTRYPOINT — RUN RESOLUTION JOB
    # --------------------------------------------------
    async def run(self) -> dict:
        """
        Resolve categories for campaigns that:
        - have no category yet, OR
        - have low-confidence inferred category
        """

        campaigns = await self._fetch_eligible_campaigns()

        processed = 0
        updated = 0
        skipped = 0

        for campaign in campaigns:
            processed += 1
            result = await self._resolve_for_campaign(campaign)

            if result == "updated":
                updated += 1
            else:
                skipped += 1

        await self.db.commit()

        return {
            "processed": processed,
            "updated": updated,
            "skipped": skipped,
        }

    # --------------------------------------------------
    # FETCH ELIGIBLE CAMPAIGNS (OPTION B)
    # --------------------------------------------------
    async def _fetch_eligible_campaigns(self) -> List[Campaign]:
        """
        Campaigns without a category OR with low-confidence inferred category.
        """

        result = await self.db.execute(
            select(Campaign)
            .outerjoin(
                CampaignCategoryMap,
                CampaignCategoryMap.campaign_id == Campaign.id,
            )
            .where(
                (CampaignCategoryMap.id.is_(None))
                | (CampaignCategoryMap.confidence_score < self.MIN_CONFIDENCE)
            )
        )

        return result.scalars().all()

    # --------------------------------------------------
    # RESOLVE SINGLE CAMPAIGN
    # --------------------------------------------------
    async def _resolve_for_campaign(self, campaign: Campaign) -> str:
        """
        Apply inference + governance rules for a single campaign.
        """

        # Load existing category map (if any)
        result = await self.db.execute(
            select(CampaignCategoryMap).where(
                CampaignCategoryMap.campaign_id == campaign.id
            )
        )
        category_map: Optional[CampaignCategoryMap] = result.scalar_one_or_none()

        # Always run inference (ML always thinks)
        inference = await self.inference_service.infer_category(
            db=self.db,
            campaign_id=str(campaign.id),
        )

        inferred_category = inference.get("inferred_category")
        confidence = inference.get("confidence_score", 0.0)

        # --------------------------------------------------
        # RULE 1 — USER CATEGORY ALWAYS WINS
        # --------------------------------------------------
        if category_map and category_map.user_category:
            # Still update inferred fields for audit
            category_map.inferred_category = inferred_category
            category_map.confidence_score = confidence
            category_map.source = CategorySource.USER
            category_map.updated_at = self._now()
            return "skipped"

        # --------------------------------------------------
        # RULE 2 — ACCEPT HIGH-CONFIDENCE ML
        # --------------------------------------------------
        if inferred_category and confidence >= self.MIN_CONFIDENCE:
            if not category_map:
                category_map = CampaignCategoryMap(
                    campaign_id=campaign.id,
                    user_category=None,
                    inferred_category=inferred_category,
                    final_category=inferred_category,
                    confidence_score=confidence,
                    source=CategorySource.INFERRED,
                )
                self.db.add(category_map)
            else:
                category_map.inferred_category = inferred_category
                category_map.final_category = inferred_category
                category_map.confidence_score = confidence
                category_map.source = CategorySource.INFERRED
                category_map.updated_at = self._now()

            return "updated"

        # --------------------------------------------------
        # RULE 3 — LOW CONFIDENCE → DO NOTHING
        # --------------------------------------------------
        if category_map:
            category_map.inferred_category = inferred_category
            category_map.confidence_score = confidence
            category_map.updated_at = self._now()

        return "skipped"

    # --------------------------------------------------
    # UTILS
    # --------------------------------------------------
    @staticmethod
    def _now():
        from datetime import datetime

        return datetime.utcnow()
