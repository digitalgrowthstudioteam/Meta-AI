from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
import enum

from app.core.database import Base


# =========================================================
# CATEGORY SOURCE ENUM
# =========================================================
class CategorySource(str, enum.Enum):
    USER = "user"
    INFERRED = "inferred"
    HYBRID = "hybrid"


# =========================================================
# CAMPAIGN ↔ CATEGORY RESOLUTION MAP
# =========================================================
class CampaignCategoryMap(Base):
    """
    Tracks how a campaign's business category was determined.

    - user_category: explicitly set by user (account-level or later override)
    - inferred_category: ML-inferred category
    - final_category: resolved category used for learning
    - confidence_score: confidence in final_category (0–1)
    - source: user | inferred | hybrid

    This table is the foundation for:
    - Cross-user category learning
    - Industry benchmarks
    - Strategy recommendations
    """

    __tablename__ = "campaign_category_map"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -------------------------
    # CATEGORY SOURCES
    # -------------------------
    user_category: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Category provided by user (if any)",
    )

    inferred_category: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Category inferred by ML",
    )

    final_category: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Resolved category used for ML learning",
    )

    source: Mapped[CategorySource] = mapped_column(
        Enum(
            CategorySource,
            name="categorysource",
            native_enum=True,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    confidence_score: Mapped[float] = mapped_column(
        nullable=False,
        doc="Confidence score for final_category (0–1)",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Ensure one active category mapping per campaign
Index(
    "ux_campaign_category_map_campaign",
    CampaignCategoryMap.campaign_id,
    unique=True,
)
