from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class AudienceInsight(Base):
    __tablename__ = "audience_insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id")
    )

    suggestion_type: Mapped[str] = mapped_column(String)  # KEEP / PAUSE / EXPAND
    reason: Mapped[str] = mapped_column(String)
    confidence_score: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
