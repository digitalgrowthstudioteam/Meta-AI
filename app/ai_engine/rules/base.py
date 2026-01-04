from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.ai_engine.models.action_models import (
    AIAction,
    ExplainabilityContext,
    ReasoningStep,
)


class BaseRule(ABC):
    """
    Base interface for all AI rules.

    Phase 10:
    - Provides explainability helpers
    - Enforces rule identity
    - Enables reasoning timeline
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
        """
        Construct explainability context consistently across rules.
        """

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
        """
        Attach explainability context to an AIAction.
        """

        action.explainability = self._build_explainability(
            steps=steps,
            benchmark_used=benchmark_used,
            trust_note=trust_note,
            evidence=evidence,
        )
        return action

    # -----------------------------------------
    # RULE CONTRACT
    # -----------------------------------------
    @abstractmethod
    async def evaluate(self, *args, **kwargs) -> List[AIAction]:
        """
        Evaluate rule and return zero or more AIAction objects.
        """
        raise NotImplementedError
