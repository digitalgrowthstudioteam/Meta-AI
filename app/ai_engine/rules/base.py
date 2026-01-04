from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.models.action_models import (
    AIAction,
    ExplainabilityContext,
    ReasoningStep,
    ConfidenceScore,
)
from app.ai_engine.models.ai_action_feedback import (
    AIActionFeedback,
    ActionApprovalStatus,
)


class BaseRule(ABC):
    """
    Base interface for all AI rules.

    Phase 12:
    - Feedback-weighted confidence
    - Trust-aware rule calibration
    """

    # -----------------------------------------
    # RULE IDENTITY (AUTO)
    # -----------------------------------------
    @property
    def rule_name(self) -> str:
        return self.__class__.__name__

    # -----------------------------------------
    # EXPLAINABILITY HELPERS
    # -----------------------------------------
    def _build_explainability(
        self,
        *,
        steps: List[str],
        benchmark_used: bool = False,
        trust_note: Optional[str] = None,
        evidence=None,
    ) -> ExplainabilityContext:

        reasoning_steps = [
            ReasoningStep(
                step=step,
                evidence=evidence,
                timestamp=datetime.utcnow(),
            )
            for step in steps
        ]

        return ExplainabilityContext(
            rule_name=self.rule_name,
            decision_path=reasoning_steps,
            benchmark_used=benchmark_used,
            trust_note=trust_note,
        )

    def attach_explainability(
        self,
        action: AIAction,
        *,
        steps: List[str],
        benchmark_used: bool = False,
        trust_note: Optional[str] = None,
        evidence=None,
    ) -> AIAction:

        action.explainability = self._build_explainability(
            steps=steps,
            benchmark_used=benchmark_used,
            trust_note=trust_note,
            evidence=evidence,
        )
        return action

    # -----------------------------------------
    # PHASE 12 — FEEDBACK-WEIGHTED CONFIDENCE
    # -----------------------------------------
    async def calibrate_confidence(
        self,
        *,
        db: AsyncSession,
        base_score: float,
        campaign_id,
        action_type: str,
    ) -> ConfidenceScore:
        """
        Adjust confidence using historical approval + helpful feedback.
        """

        stmt = select(AIActionFeedback).where(
            AIActionFeedback.campaign_id == campaign_id,
            AIActionFeedback.rule_name == self.rule_name,
            AIActionFeedback.action_type == action_type,
            AIActionFeedback.approval_status == ActionApprovalStatus.APPROVED,
        )

        result = await db.execute(stmt)
        feedback_rows = result.scalars().all()

        if not feedback_rows:
            return ConfidenceScore(
                score=base_score,
                reason="No historical feedback; base confidence used",
            )

        helpful = [f for f in feedback_rows if f.is_helpful is True]
        unhelpful = [f for f in feedback_rows if f.is_helpful is False]

        total = len(helpful) + len(unhelpful)
        if total == 0:
            return ConfidenceScore(
                score=base_score,
                reason="No helpfulness signal; base confidence used",
            )

        helpful_ratio = len(helpful) / total

        calibrated_score = round(
            min(1.0, max(0.0, base_score * (0.7 + helpful_ratio))),
            2,
        )

        return ConfidenceScore(
            score=calibrated_score,
            reason=f"Adjusted using {total} approved feedback signals",
        )

    # -----------------------------------------
    # RULE CONTRACT
    # -----------------------------------------
    @abstractmethod
    async def evaluate(self, *args, **kwargs) -> List[AIAction]:
        raise NotImplementedError
