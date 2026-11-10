"""Minimal unique daily account views with bounded retention indexes."""

import sqlalchemy as sa

from alembic import op

revision = "0034_canvas_views"
down_revision = "0033_board_subscriptions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canvas_views",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("viewed_on", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("canvas_id", "user_id", "viewed_on"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_canvas_views_window", "canvas_views", ["canvas_id", "viewed_on"])
    op.create_index("ix_canvas_views_expiry", "canvas_views", ["viewed_on"])
    op.create_index("ix_canvas_views_user", "canvas_views", ["user_id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM canvas_views")):
        raise RuntimeError("Canvas views remain; refusing destructive downgrade.")
    op.drop_table("canvas_views")
