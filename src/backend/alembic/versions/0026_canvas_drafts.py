"""Canvas drafts and documents with Board/Shelf integrity."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0026_canvas_drafts"
down_revision = "0025_board_member_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canvases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("shelf_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.String(500), server_default="", nullable=False),
        sa.Column("status", sa.String(12), server_default="draft", nullable=False),
        sa.Column("visibility", sa.String(10), server_default="members", nullable=False),
        sa.Column("revision", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("trashed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft','trashed')", name="ck_canvas_status"),
        sa.CheckConstraint("visibility IN ('public','members')", name="ck_canvas_visibility"),
        sa.CheckConstraint("revision >= 0", name="ck_canvas_revision"),
        sa.CheckConstraint(
            "(status = 'draft' AND trashed_at IS NULL) OR (status = 'trashed' AND trashed_at IS NOT NULL)",
            name="ck_canvas_trash_state",
        ),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["board_id", "shelf_id"],
            ["shelves.board_id", "shelves.id"],
            ondelete="RESTRICT",
            name="fk_canvas_shelf",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvases_board_shelf", "canvases", ["board_id", "shelf_id"])
    op.create_index("ix_canvases_author_id", "canvases", ["author_id"])
    op.create_table(
        "canvas_documents",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column(
            "document",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("revision", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision >= 0", name="ck_canvas_document_revision"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("canvas_id"),
    )


def downgrade() -> None:
    op.drop_table("canvas_documents")
    op.drop_index("ix_canvases_author_id", table_name="canvases")
    op.drop_index("ix_canvases_board_shelf", table_name="canvases")
    op.drop_table("canvases")
