"""Global Meta Ad Accounts + User Access Mapping

Revision ID: 9b5_global_meta_accounts
Revises: 
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "9b5_global_meta_accounts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # -----------------------------------------------------
    # 1. Refactor meta_ad_accounts (GLOBAL)
    # -----------------------------------------------------

    # Drop user_id column (ownership removed)
    with op.batch_alter_table("meta_ad_accounts") as batch_op:
        batch_op.drop_column("user_id")

        batch_op.create_unique_constraint(
            "uq_meta_ad_accounts_meta_account_id",
            ["meta_account_id"],
        )

    # -----------------------------------------------------
    # 2. Create user_meta_ad_accounts (ACCESS MAPPING)
    # -----------------------------------------------------

    op.create_table(
        "user_meta_ad_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "meta_ad_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meta_ad_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(),
            nullable=False,
            server_default="owner",
        ),
        sa.Column(
            "connected_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "meta_ad_account_id",
            name="uq_user_meta_ad_account_access",
        ),
    )


def downgrade():
    # -----------------------------------------------------
    # Reverse user_meta_ad_accounts
    # -----------------------------------------------------
    op.drop_table("user_meta_ad_accounts")

    # -----------------------------------------------------
    # Restore meta_ad_accounts ownership
    # -----------------------------------------------------
    with op.batch_alter_table("meta_ad_accounts") as batch_op:
        batch_op.drop_constraint(
            "uq_meta_ad_accounts_meta_account_id",
            type_="unique",
        )

        batch_op.add_column(
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
            )
        )
