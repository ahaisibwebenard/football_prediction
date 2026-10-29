"""Initial PredictPro schema, frozen SQL snapshot."""

from pathlib import Path
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    sql = Path(__file__).with_name("001_schema.sql").read_text()
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    for table in (
        "rate_buckets",
        "settings",
        "audit",
        "notifications",
        "follows",
        "favorites",
        "picks",
        "predictions",
        "matches",
        "teams",
        "leagues",
        "resets",
        "sessions",
        "users",
    ):
        op.drop_table(table)
