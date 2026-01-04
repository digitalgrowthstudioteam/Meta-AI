from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.ai_engine.models.campaign_category_map import (
    CampaignCategoryMap,
    CategorySource,
)
from app.ai_engine.services.category_inference_service import (
    CategoryInferenceService,
)


class CategoryPersistenceService:
    """
    Persists inferred campaign category into campaign_category_map.

    Priority:
    - User category > inferred category
    - Hybrid when both exist
    """

    MIN_INFERENCE_CONFIDENCE = 0.6

    def __init__(self, db: AsyncSession):
        self.db = db
        self.inference = CategoryInferenceService()

    async def persist_for_campaign(
        self,
        *,
        campaign_id: str,
    ) -> None:
        """
        Infer and persist category for a single campaign.
        """

        inference = await self.inference.infer_category(
            db=self.db,
            campaign_id=campaign_id,
        )

        inferred_category = inference.get("inferred_category")
        inferred_confidence = inference.get("confidence_score", 0.0)

        if not inferred_category or inferred_confidence < self.MIN_INFERENCE_CONFIDENCE:
            return

        # --------------------------------------------------
        # Load existing mapping (if any)
        # --------------------------------------------------
        result = await self.db.execute(
            select(CampaignCategoryMap).where(
                CampaignCategoryMap.campaign_id == campaign_id
            )
        )
        mapping = result.scalar_one_or_none()

        now = datetime.utcnow()

        # --------------------------------------------------
        # CASE 1 — Mapping does not exist
        # --------------------------------------------------
        if not mapping:
            self.db.add(
                CampaignCategoryMap(
                    campaign_id=campaign_id,
                    user_category=None,
                    inferred_category=inferred_category,
                    final_category=inferred_category,
                    source=CategorySource.INFERRED,
                    confidence_score=inferred_confidence,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self.db.commit()
            return

        # --------------------------------------------------
        # CASE 2 — User category exists → HYBRID
        # --------------------------------------------------
        if mapping.user_category:
            mapping.inferred_category = inferred_category
            mapping.final_category = mapping.user_category
            mapping.source = CategorySource.HYBRID
            mapping.confidence_score = max(
                mapping.confidence_score, inferred_confidence
            )
            mapping.updated_at = now
            await self.db.commit()
            return

        # --------------------------------------------------
        # CASE 3 — Inferred overwrite / update
        # --------------------------------------------------
        mapping.inferred_category = inferred_category
        mapping.final_category = inferred_category
        mapping.source = CategorySource.INFERRED
        mapping.confidence_score = inferred_confidence
        mapping.updated_at = now

        await self.db.commit()
