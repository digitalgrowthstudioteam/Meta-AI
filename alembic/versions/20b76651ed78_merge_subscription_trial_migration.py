"""merge subscription trial migration

Revision ID: 20b76651ed78
Revises: 1ea4fa54a091, 688791acd54f
Create Date: 2026-01-02 21:23:50.874305

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20b76651ed78'
down_revision = ('1ea4fa54a091', '688791acd54f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
