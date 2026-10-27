"""Support Board member and audit keyset pagination."""

from alembic import op

revision = "0025_board_member_indexes"
down_revision = "0024_board_creation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_board_members_page", "board_members", ["board_id", "joined_at", "user_id"])
    op.create_index(
        "ix_board_member_audit_page", "board_member_audit", ["board_id", "created_at", "id"]
    )


def downgrade():
    op.drop_index("ix_board_member_audit_page", table_name="board_member_audit")
    op.drop_index("ix_board_members_page", table_name="board_members")
