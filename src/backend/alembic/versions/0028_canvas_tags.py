"""Global free tags and Canvas links without rebuilding existing content tables."""

import sqlalchemy as sa

from alembic import op

revision = "0028_canvas_tags"
down_revision = "0027_canvas_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column(
            "normalized_name",
            sa.String(80).with_variant(sa.String(80, collation="C"), "postgresql"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(name) BETWEEN 1 AND 40", name="ck_tag_name_length"),
        sa.CheckConstraint(
            "length(normalized_name) BETWEEN 1 AND 80", name="ck_tag_normalized_name_length"
        ),
    )
    op.create_index("uq_tag_normalized_name", "tags", ["normalized_name"], unique=True)
    op.create_table(
        "canvas_tags",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("canvas_id", "tag_id"),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_canvas_tags_tag", "canvas_tags", ["tag_id"])


def downgrade() -> None:
    op.drop_table("canvas_tags")
    op.drop_table("tags")
