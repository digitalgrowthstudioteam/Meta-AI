from enum import Enum
from typing import List, Optional
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

    # Phase 9.5 — benchmark awareness
    source: Optional[str] = Field(
        default="campaign",
        description="campaign | industry | category",
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
# CONFIDENCE MODEL
# =========================================================
class ConfidenceScore(BaseModel):
    """
    Rule-based confidence score (0–1).

    Phase 9.5:
    - Boosted when industry / category benchmarks confirm
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

    Campaign-scoped decision backed by:
    - Aggregated metrics
    - Breakdown intelligence
    - Industry / category benchmarks (Phase 9.5)
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
