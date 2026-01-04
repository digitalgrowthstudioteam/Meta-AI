from datetime import datetime, date
import uuid

from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Date,
    Float,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AdminOverride(Base):
    """
    Temporary, auditable admin-level overrides.
    Never mutates plans or subscriptions.
    """

    __tablename__ = "admin_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extra_ai_campaigns = Column(Integer, default=0, nullable=False)

    force_ai_enabled = Column(Boolean, default=False, nullable=False)

    override_expires_at = Column(DateTime(timezone=True), nullable=True)

    reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


class CampaignDailyMetrics(Base):
    """
    PHASE 6.5 — RAW META INSIGHTS (CAMPAIGN LEVEL)

    Immutable, idempotent daily metrics.
    Used ONLY for analytics & AI reads.
    """

    __tablename__ = "campaign_daily_metrics"
    __table_args__ = (
        UniqueConstraint("campaign_id", "date", name="uq_campaign_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False, index=True)

    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)

    leads = Column(Integer, nullable=False, default=0)
    purchases = Column(Integer, nullable=False, default=0)
    revenue = Column(Float, nullable=False, default=0.0)

    ctr = Column(Float, nullable=True)
    cpl = Column(Float, nullable=True)
    cpa = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
