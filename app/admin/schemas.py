from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, Optional


# =====================================================
# ADMIN OVERRIDES (EXISTING)
# =====================================================
class AdminOverrideCreate(BaseModel):
    user_id: UUID
    extra_ai_campaigns: int = 0
    force_ai_enabled: bool = False
    override_expires_at: datetime | None = None
    reason: str | None = None


class AdminOverrideResponse(BaseModel):
    id: UUID
    user_id: UUID
    extra_ai_campaigns: int
    force_ai_enabled: bool
    override_expires_at: datetime | None
    reason: str | None
    created_at: datetime


# =====================================================
# PHASE 7 — ADMIN PRICING CONFIG SCHEMAS
# =====================================================
class AdminPricingConfigBase(BaseModel):
    plan_pricing: Dict[str, Any]
    slot_packs: Dict[str, Any]
    currency: str
    tax_percentage: int
    invoice_prefix: str
    invoice_notes: Optional[str] = None
    razorpay_mode: str


class AdminPricingConfigCreate(AdminPricingConfigBase):
    reason: str


class AdminPricingConfigResponse(AdminPricingConfigBase):
    id: UUID
    version: int
    is_active: bool
    created_by_admin_id: UUID
    created_at: datetime
    activated_at: Optional[datetime] = None

# =====================================================
# PHASE 10 — USAGE OVERRIDES (NEW)
# =====================================================

class UsageOverrideUpsert(BaseModel):
    key: str  # campaigns | ad_accounts | team_members | credits
    value: int
    expires_at: datetime | None = None
    reason: str


class UsageOverrideDelete(BaseModel):
    key: str
    reason: str


class UsageOverrideResponse(BaseModel):
    key: str
    value: int
    expires_at: datetime | None
    updated_by: UUID | None
    updated_at: datetime | None

