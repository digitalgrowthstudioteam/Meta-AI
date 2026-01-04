from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# =========================================================
# ACTION TYPES (WHAT AI CAN SUGGEST)
# =========================================================
class AIActionType(str, Enum):
    SCALE_CAMPAIGN = "SCALE_CAMPAIGN"
    REDUCE_BUDGET = "REDUCE_BUDGET"
    PAUSE_CAMPAIGN = "PAUSE_CAMPAIGN"

    SHIFT_CREATIVE = "SHIFT_CREATIVE"
    SHIFT_PLACEMENT = "SHIFT_PLACEMENT"
    SHIFT_AUDIENCE = "SHIFT_AUDIENCE"

    NO_ACTION = "NO_ACTION"


# =========================================================
# EVIDENCE MODELS (WHY AI IS SAYING THIS)
# =========================================================
class MetricEvidence(BaseModel):
    """
    Numeric evidence backing a recommendation.
    """

    metric: str = Field(..., example="cpl")
    window: str = Field(..., example="7D")
    value: float = Field(..., example=120.5)
    baseline: Optional[float] = Field(
        None, example=95.2, description="Comparison baseline"
    )
    delta_pct: Optional[float] = Field(
        None, example=26.5, description="% change vs baseline"
    )


class BreakdownEvidence(BaseModel):
    """
    Evidence from breakdown-level performance.
    """

    dimension: str = Field(
        ..., example="ad_id", description="ad_id | placement | age_group | region"
    )
    key: str = Field(
        ..., example="238493849384", description="Specific breakdown value"
    )
    metrics: List[MetricEvidence]


# =========================================================
# CONFIDENCE MODEL
# =========================================================
class ConfidenceScore(BaseModel):
    """
    Rule-based confidence score (0–1).
    """

    score: float = Field(..., ge=0.0, le=1.0, example=0.82)
    reason: str = Field(
        ..., example="Consistent CPL improvement across 7D and 14D windows"
    )


# =========================================================
# CORE AI ACTION MODEL
# =========================================================
class AIAction(BaseModel):
    """
    Single AI recommendation.

    Campaign-scoped decision
    backed by ad / placement / demographic evidence.
    """

    # Scope
    campaign_id: UUID

    # Action
    action_type: AIActionType

    # Human-readable explanation
    summary: str = Field(
        ..., example="Reduce budget due to rising CPL over the last 7 days"
    )

    # Quantitative evidence
    metrics: List[MetricEvidence] = []

    # Breakdown evidence (optional)
    breakdowns: List[BreakdownEvidence] = []

    # Confidence
    confidence: ConfidenceScore

    # Safety / control
    is_auto_applicable: bool = Field(
        default=False,
        description="Always false in Phase 7 (suggest-only)",
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
