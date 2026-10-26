"""Add optional unique profile handles and interest tags."""

import sqlalchemy as sa

from alembic import op

revision = "0021_profile_identity"
down_revision = "0020_inbox_deletion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("handle", sa.String(24), nullable=True))
    op.add_column(
        "users", sa.Column("interests", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
    )
    op.create_index("ix_users_handle", "users", ["handle"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_handle", table_name="users")
    op.drop_column("users", "interests")
    op.drop_column("users", "handle")
