from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


# =====================================================
# CAMPAIGN RESPONSE — PHASE 9.2 VISIBILITY
# =====================================================
class CampaignResponse(BaseModel):
    id: UUID
    name: str
    objective: str
    status: str

    # AI
    ai_active: bool
    ai_activated_at: datetime | None

    # 🔍 CATEGORY VISIBILITY (READ-ONLY)
    category: str | None
    category_confidence: float | None
    category_source: str | None


# =====================================================
# AI TOGGLE REQUEST
# =====================================================
class ToggleAIRequest(BaseModel):
    enable: bool
