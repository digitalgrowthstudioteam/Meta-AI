"""add meta oauth state (manual)

Revision ID: 897d3889e5e5
Revises: 20b76651ed78
Create Date: 2026-01-02 22:07:53.181604
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '897d3889e5e5'
down_revision = '20b76651ed78'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'meta_oauth_states',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'state',
            sa.String(),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            'is_used',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table('meta_oauth_states')
