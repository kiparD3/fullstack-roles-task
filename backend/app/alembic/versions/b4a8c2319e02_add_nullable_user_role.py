"""Add nullable role; deliberately defer existing-user backfill."""
from alembic import op
import sqlalchemy as sa

revision = "b4a8c2319e02"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("role", sa.String(16), nullable=True))
    op.create_check_constraint("ck_user_role", "user", "role IN ('manager', 'member')")


def downgrade() -> None:
    op.drop_constraint("ck_user_role", "user", type_="check")
    op.drop_column("user", "role")
