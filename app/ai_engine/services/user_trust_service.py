from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.models.ai_action_feedback import (
    AIActionFeedback,
    ActionApprovalStatus,
)


class UserTrustService:
    """
    Phase 12 — User Trust Scoring (READ-ONLY)

    Computes a trust score (0–1) per user using:
    - Approval vs rejection
    - Helpful vs not helpful signals
    """

    @staticmethod
    async def get_user_trust_score(
        *,
        db: AsyncSession,
        user_id,
    ) -> Tuple[float, str]:
        """
        Returns (trust_score, reason)
        """

        stmt = select(AIActionFeedback).where(
            AIActionFeedback.user_id == user_id
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return 0.5, "No feedback history; neutral trust applied"

        approved = [
            r for r in rows
            if r.approval_status == ActionApprovalStatus.APPROVED
        ]
        rejected = [
            r for r in rows
            if r.approval_status == ActionApprovalStatus.REJECTED
        ]

        helpful = [r for r in approved if r.is_helpful is True]
        unhelpful = [r for r in approved if r.is_helpful is False]

        total_signals = len(approved) + len(rejected)

        if total_signals == 0:
            return 0.5, "Insufficient approval signals; neutral trust applied"

        approval_ratio = len(approved) / total_signals

        helpful_ratio = (
            len(helpful) / max(1, (len(helpful) + len(unhelpful)))
        )

        # Weighted trust computation
        trust_score = round(
            min(
                1.0,
                max(
                    0.0,
                    (approval_ratio * 0.6) + (helpful_ratio * 0.4),
                ),
            ),
            2,
        )

        return (
            trust_score,
            f"Computed from {total_signals} actions "
            f"({len(approved)} approved, {len(rejected)} rejected)",
        )
