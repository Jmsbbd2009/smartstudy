"""Seed the explicit platform roles."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = "0002_roles"
down_revision = "15671c774870"
branch_labels = None
depends_on = None


def upgrade():
    roles = sa.table(
        "roles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    names = ["STUDENT", "PARENT", "TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"]
    time = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        roles,
        [
            {"id": f"00000000-0000-0000-0000-{i:012d}", "name": n, "created_at": time, "updated_at": time}
            for i, n in enumerate(names, 1)
        ],
    )


def downgrade():
    op.execute("DELETE FROM roles WHERE id LIKE '00000000-0000-0000-0000-%'")
