"""Membership-independent Board feed selections."""

import sqlalchemy as sa

from alembic import op

revision = "0033_board_subscriptions"
down_revision = "0032_canvas_comments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "board_subscriptions",
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("board_id", "user_id"),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_board_subscriptions_user", "board_subscriptions", ["user_id", "board_id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM board_subscriptions")):
        raise RuntimeError("Board subscriptions remain; refusing destructive downgrade.")
    op.drop_table("board_subscriptions")
