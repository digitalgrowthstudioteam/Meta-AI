from enum import Enum
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# =========================================================
# ACTION TYPES (WHAT AI CAN SUGGEST)
# =========================================================
class AIActionType(str, Enum):
    # Campaign-level
    SCALE_CAMPAIGN = "SCALE_CAMPAIGN"
    REDUCE_BUDGET = "REDUCE_BUDGET"
    PAUSE_CAMPAIGN = "PAUSE_CAMPAIGN"

    # Breakdown-level
    SHIFT_CREATIVE = "SHIFT_CREATIVE"
    SHIFT_PLACEMENT = "SHIFT_PLACEMENT"
    SHIFT_AUDIENCE = "SHIFT_AUDIENCE"

    # Strategy / insight only
    NO_ACTION = "NO_ACTION"


# =========================================================
# EVIDENCE MODELS
# =========================================================
class MetricEvidence(BaseModel):
    """
    Numeric evidence backing a recommendation.
    """

    metric: str = Field(..., example="roas")
    window: str = Field(..., example="7D")
    value: float = Field(..., example=2.14)

    # Optional comparison context
    baseline: Optional[float] = Field(
        None, example=2.85, description="Baseline value for comparison"
    )
    delta_pct: Optional[float] = Field(
        None, example=-24.9, description="% change vs baseline"
    )

    # Source of truth (Phase 9.5+)
    source: Literal["campaign", "industry", "category"] = Field(
        default="campaign",
        description="Origin of this metric",
    )


class BreakdownEvidence(BaseModel):
    """
    Evidence from breakdown-level performance.
    """

    dimension: str = Field(
        ...,
        example="creative_id",
        description="creative_id | placement | age_group | region | audience",
    )

    key: str = Field(
        ...,
        example="238493849384",
        description="Specific breakdown value",
    )

    metrics: List[MetricEvidence]


# =========================================================
# REASONING & EXPLAINABILITY (PHASE 10)
# =========================================================
class ReasoningStep(BaseModel):
    """
    Atomic reasoning step for explainability timeline.
    """

    step: str = Field(..., example="7D ROAS dropped below 30D baseline")
    evidence: Optional[List[MetricEvidence]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplainabilityContext(BaseModel):
    """
    Human + UI consumable explanation context.
    """

    rule_name: str = Field(
        ..., example="SalesROASDropRule"
    )

    decision_path: List[ReasoningStep] = Field(
        default_factory=list,
        description="Ordered reasoning steps",
    )

    benchmark_used: bool = Field(
        default=False,
        description="Was industry/category benchmark used?",
    )

    trust_note: Optional[str] = Field(
        None,
        example="Decision confirmed by industry benchmark with high sample size",
    )


# =========================================================
# CONFIDENCE MODEL
# =========================================================
class ConfidenceScore(BaseModel):
    """
    Rule-based confidence score (0–1).
    """

    score: float = Field(..., ge=0.0, le=1.0, example=0.82)

    reason: str = Field(
        ...,
        example="Confirmed by industry benchmark and stable 30D trend",
    )


# =========================================================
# CORE AI ACTION MODEL
# =========================================================
class AIAction(BaseModel):
    """
    Single AI recommendation.

    Phase 10:
    - Fully explainable
    - Trust & reasoning attached
    """

    # Scope
    campaign_id: UUID

    # Action
    action_type: AIActionType

    # Human-readable explanation
    summary: str = Field(
        ..., example="Reduce budget due to ROAS decay vs industry benchmark"
    )

    # Metric evidence (campaign / benchmark)
    metrics: List[MetricEvidence] = []

    # Breakdown evidence (creative / placement / audience)
    breakdowns: List[BreakdownEvidence] = []

    # Explainability (NEW)
    explainability: Optional[ExplainabilityContext] = None

    # Confidence
    confidence: ConfidenceScore

    # Automation safety
    is_auto_applicable: bool = Field(
        default=False,
        description="Always false until auto-execution phase",
    )

    # Audit
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================
# ACTION SET (MULTIPLE PER CAMPAIGN)
# =========================================================
class AIActionSet(BaseModel):
    """
    Collection of AI actions for a campaign.
    """

    campaign_id: UUID
    actions: List[AIAction]
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
