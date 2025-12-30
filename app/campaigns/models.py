from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    meta_campaign_id: Mapped[str] = mapped_column(String)

    ad_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meta_ad_accounts.id")
    )

    name: Mapped[str] = mapped_column(String)
    objective: Mapped[str] = mapped_column(String)  # LEAD / SALES
    status: Mapped[str] = mapped_column(String)

    ai_active: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
