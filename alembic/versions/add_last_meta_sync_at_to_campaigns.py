"""add last_meta_sync_at to campaigns

Revision ID: add_last_meta_sync_at
Revises: <PUT_PREVIOUS_HEAD_REVISION_ID_HERE>
Create Date: 2026-01-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_last_meta_sync_at"
down_revision = "<PUT_PREVIOUS_HEAD_REVISION_ID_HERE>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column(
            "last_meta_sync_at",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "last_meta_sync_at")
