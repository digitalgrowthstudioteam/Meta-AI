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
# EXECUTION & APPROVAL GUARDRAILS (PHASE 11)
# =========================================================
class ActionApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


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

    baseline: Optional[float] = Field(
        None, example=2.85, description="Baseline value for comparison"
    )
    delta_pct: Optional[float] = Field(
        None, example=-24.9, description="% change vs baseline"
    )

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
    step: str = Field(..., example="7D ROAS dropped below 30D baseline")
    evidence: Optional[List[MetricEvidence]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplainabilityContext(BaseModel):
    rule_name: str = Field(..., example="SalesROASDropRule")

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
# CONFIDENCE MODEL (PHASE 21)
# =========================================================
class ConfidenceBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, example=0.82)

    band: Optional[ConfidenceBand] = Field(
        None,
        description="LOW | MEDIUM | HIGH (Phase 21)",
    )

    reason: str = Field(
        ...,
        example="Confirmed by industry benchmark and stable 30D trend",
    )


# =========================================================
# CORE AI ACTION MODEL (PHASE 11 SAFE)
# =========================================================
class AIAction(BaseModel):
    """
    Single AI recommendation with execution guardrails.
    """

    # Scope
    campaign_id: UUID

    # Action
    action_type: AIActionType

    # Human-readable explanation
    summary: str = Field(
        ..., example="Reduce budget due to ROAS decay vs industry benchmark"
    )

    # Evidence
    metrics: List[MetricEvidence] = []
    breakdowns: List[BreakdownEvidence] = []

    # Explainability
    explainability: Optional[ExplainabilityContext] = None

    # Confidence (Phase 21 exposed)
    confidence: ConfidenceScore

    # =====================================================
    # EXECUTION GUARDRAILS (PHASE 11)
    # =====================================================
    approval_status: ActionApprovalStatus = Field(
        default=ActionApprovalStatus.DRAFT,
        description="Human approval lifecycle status",
    )

    requires_human_approval: bool = Field(
        default=True,
        description="Always true until auto-apply is unlocked",
    )

    approved_by_user_id: Optional[UUID] = Field(
        default=None,
        description="User who approved this action",
    )

    approved_at: Optional[datetime] = None

    approval_expires_at: Optional[datetime] = Field(
        default=None,
        description="Action becomes invalid after this time",
    )

    max_budget_change_pct: Optional[float] = Field(
        default=None,
        description="Hard safety cap for budget changes",
    )

    rollback_supported: bool = Field(
        default=True,
        description="Whether rollback metadata is available",
    )

    # Hard safety lock (cannot be bypassed)
    auto_execution_blocked: bool = Field(
        default=True,
        description="System-level block on auto execution",
    )

    # Audit
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================
# ACTION SET (MULTIPLE PER CAMPAIGN)
# =========================================================
class AIActionSet(BaseModel):
    campaign_id: UUID
    actions: List[AIAction]
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
