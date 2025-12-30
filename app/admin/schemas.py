from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


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
