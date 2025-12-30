from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class AIAction(Base):
    __tablename__ = "ai_actions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id")
    )

    action_type: Mapped[str] = mapped_column(String)

    before_state: Mapped[dict] = mapped_column(JSON)
    after_state: Mapped[dict] = mapped_column(JSON)

    confidence_level: Mapped[str] = mapped_column(String)  # LOW / MEDIUM / HIGH
    executed_mode: Mapped[str] = mapped_column(String)     # SUGGEST / AUTO

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
