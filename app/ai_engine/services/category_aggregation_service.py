from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime


class CategoryAggregationService:
    """
    Aggregates breakdown-level ML features across all users
    into global category intelligence.

    SAFE:
    - High-confidence categories only
    - Minimum sample size enforced
    - Fully anonymized
    - Idempotent
    """

    MIN_CONFIDENCE = 0.70
    MIN_SAMPLE_SIZE = 20

    async def run(
        self,
        *,
        db: AsyncSession,
        window_type: str,
    ) -> None:
        """
        Aggregate category stats for a given window (30d / 90d / lifetime).
        """

        await db.execute(
            text(
                """
                INSERT INTO ml_category_breakdown_stats (
                    business_category,
                    window_type,
                    age_range,
                    gender,
                    city,
                    placement,
                    device,
                    avg_ctr,
                    avg_cpl,
                    avg_cpa,
                    avg_roas,
                    median_roas,
                    sample_size,
                    confidence_score,
                    last_updated_at
                )
                SELECT
                    ccm.final_category AS business_category,
                    :window_type AS window_type,
                    mbf.age_range,
                    mbf.gender,
                    mbf.city,
                    mbf.placement,
                    mbf.device,

                    AVG(mbf.ctr) AS avg_ctr,
                    AVG(mbf.cpl) AS avg_cpl,
                    AVG(mbf.cpa) AS avg_cpa,
                    AVG(mbf.roas) AS avg_roas,
                    PERCENTILE_CONT(0.5)
                        WITHIN GROUP (ORDER BY mbf.roas) AS median_roas,

                    COUNT(DISTINCT mbf.campaign_id) AS sample_size,

                    LEAST(
                        1.0,
                        COUNT(DISTINCT mbf.campaign_id)::float / 100.0
                    ) AS confidence_score,

                    :now AS last_updated_at
                FROM ml_breakdown_features mbf
                JOIN campaign_category_map ccm
                    ON ccm.campaign_id = mbf.campaign_id
                WHERE
                    mbf.window_type = :window_type
                    AND ccm.confidence_score >= :min_confidence
                GROUP BY
                    ccm.final_category,
                    mbf.age_range,
                    mbf.gender,
                    mbf.city,
                    mbf.placement,
                    mbf.device
                HAVING
                    COUNT(DISTINCT mbf.campaign_id) >= :min_sample_size
                ON CONFLICT (
                    business_category,
                    window_type,
                    age_range,
                    gender,
                    city,
                    placement,
                    device
                )
                DO UPDATE SET
                    avg_ctr = EXCLUDED.avg_ctr,
                    avg_cpl = EXCLUDED.avg_cpl,
                    avg_cpa = EXCLUDED.avg_cpa,
                    avg_roas = EXCLUDED.avg_roas,
                    median_roas = EXCLUDED.median_roas,
                    sample_size = EXCLUDED.sample_size,
                    confidence_score = EXCLUDED.confidence_score,
                    last_updated_at = EXCLUDED.last_updated_at
                """
            ),
            {
                "window_type": window_type,
                "min_confidence": self.MIN_CONFIDENCE,
                "min_sample_size": self.MIN_SAMPLE_SIZE,
                "now": datetime.utcnow(),
            },
        )

        await db.commit()
