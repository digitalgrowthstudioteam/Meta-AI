"""Merge meta global ad accounts migration

Revision ID: 1da1c96ad146
Revises: 79356bb33da2, 9b5_global_meta_accounts
Create Date: 2025-12-31 06:50:35.218538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1da1c96ad146'
down_revision = ('79356bb33da2', '9b5_global_meta_accounts')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
