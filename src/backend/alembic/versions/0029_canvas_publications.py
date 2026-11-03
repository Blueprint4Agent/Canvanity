"""Independent publication state without rebuilding the populated Canvas parent."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0029_canvas_publications"
down_revision = "0028_canvas_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canvas_publication_counters",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.BigInteger(), server_default="0", nullable=False),
        sa.CheckConstraint("revision >= 0", name="ck_publication_counter_revision"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("canvas_id"),
    )
    op.create_table(
        "canvas_publications",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("publication_revision", sa.BigInteger(), nullable=False),
        sa.Column("source_metadata_revision", sa.BigInteger(), nullable=False),
        sa.Column("source_document_revision", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("visibility", sa.String(10), nullable=False),
        sa.Column(
            "document", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("publication_revision > 0", name="ck_publication_revision"),
        sa.CheckConstraint(
            "source_metadata_revision >= 0 AND source_document_revision >= 0",
            name="ck_publication_source_revisions",
        ),
        sa.CheckConstraint("visibility IN ('public','members')", name="ck_publication_visibility"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("canvas_id"),
    )
    op.create_index(
        "ix_canvas_publications_published", "canvas_publications", ["published_at", "canvas_id"]
    )
    op.create_table(
        "canvas_publication_tags",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0 AND position < 10", name="ck_publication_tag_position"),
        sa.UniqueConstraint("canvas_id", "position", name="uq_publication_tag_position"),
        sa.ForeignKeyConstraint(
            ["canvas_id"], ["canvas_publications.canvas_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("canvas_id", "tag_id"),
    )
    op.create_index("ix_publication_tags_tag", "canvas_publication_tags", ["tag_id", "canvas_id"])


def downgrade() -> None:
    connection = op.get_bind()
    if (
        connection.scalar(sa.text("SELECT count(*) FROM canvas_publication_counters"))
        or (connection.scalar(sa.text("SELECT count(*) FROM canvas_publications")))
        or connection.scalar(
            sa.text("SELECT count(*) FROM canvas_asset_refs WHERE scope = 'publication'")
        )
    ):
        raise RuntimeError(
            "Publication history or references remain; refusing destructive downgrade."
        )
    op.drop_table("canvas_publication_tags")
    op.drop_table("canvas_publications")
    op.drop_table("canvas_publication_counters")
