"""Add country labels to competitions."""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("leagues", sa.Column("country", sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column("leagues", "country")