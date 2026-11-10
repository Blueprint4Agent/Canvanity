"""Unique per-account Canvas reactions, independent of document/publication clocks."""

import sqlalchemy as sa

from alembic import op

revision = "0031_canvas_likes"
down_revision = "0030_board_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canvas_likes",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("canvas_id", "user_id"),
    )
    op.create_index("ix_canvas_likes_user", "canvas_likes", ["user_id"])


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM canvas_likes")):
        raise RuntimeError("Canvas likes remain; refusing destructive downgrade.")
    op.drop_table("canvas_likes")
