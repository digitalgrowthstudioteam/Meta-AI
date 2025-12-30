from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    objective: str
    status: str
    ai_active: bool
    ai_activated_at: datetime | None


class ToggleAIRequest(BaseModel):
    enable: bool
