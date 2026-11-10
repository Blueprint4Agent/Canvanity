"""Independent comment state, clocks and deletion boundaries."""

import sqlalchemy as sa

from alembic import op

revision = "0032_canvas_comments"
down_revision = "0031_canvas_likes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canvas_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.String(5000), nullable=False),
        sa.Column("status", sa.String(7), server_default="visible", nullable=False),
        sa.Column("revision", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("moderated_by", sa.Integer(), nullable=True),
        sa.Column("moderation_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["moderated_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('visible','hidden','deleted')", name="ck_canvas_comment_status"
        ),
        sa.CheckConstraint("revision >= 0", name="ck_canvas_comment_revision"),
        sa.CheckConstraint(
            "(status = 'deleted' AND body = '') OR (status <> 'deleted' AND length(body) BETWEEN 1 AND 5000)",
            name="ck_canvas_comment_body",
        ),
    )
    op.create_index("ix_canvas_comments_page", "canvas_comments", ["canvas_id", "created_at", "id"])
    op.create_index("ix_canvas_comments_author", "canvas_comments", ["author_id"])
    op.create_index("ix_canvas_comments_moderator", "canvas_comments", ["moderated_by"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM canvas_comments")):
        raise RuntimeError("Canvas comments remain; refusing destructive downgrade.")
    op.drop_table("canvas_comments")
