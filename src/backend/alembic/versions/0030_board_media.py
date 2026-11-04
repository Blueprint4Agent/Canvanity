"""Board-owned media and ready slot references without altering existing parents."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0030_board_media"
down_revision = "0029_canvas_publications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "board_media_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("slot", sa.String(6), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("storage_fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "storage_location",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(50), server_default="image/webp", nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("frame_count", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(10), server_default="pending", nullable=False),
        sa.Column("upload_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("storage_fingerprint", "object_key", name="uq_board_media_object"),
        sa.UniqueConstraint("board_id", "slot", "id", "state", name="uq_board_media_ref_target"),
        sa.CheckConstraint("slot IN ('avatar','cover')", name="ck_board_media_slot"),
        sa.CheckConstraint("state IN ('pending','ready','deleting')", name="ck_board_media_state"),
        sa.CheckConstraint(
            "byte_size > 0 AND width > 0 AND height > 0 AND frame_count > 0",
            name="ck_board_media_dimensions",
        ),
        sa.CheckConstraint(
            "content_type = 'image/webp' AND byte_size <= 8388608 AND frame_count <= 100 AND CAST(width AS BIGINT) * height * frame_count <= 16000000",
            name="ck_board_media_bounds",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_board_media_owner", "board_media_assets", ["owner_id"])
    op.create_index("ix_board_media_board_state", "board_media_assets", ["board_id", "state"])
    op.create_table(
        "board_media_refs",
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("slot", sa.String(6), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("asset_state", sa.String(10), server_default="ready", nullable=False),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["board_id", "slot", "asset_id", "asset_state"],
            [
                "board_media_assets.board_id",
                "board_media_assets.slot",
                "board_media_assets.id",
                "board_media_assets.state",
            ],
            name="fk_board_media_ref",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("slot IN ('avatar','cover')", name="ck_board_media_ref_slot"),
        sa.CheckConstraint("asset_state = 'ready'", name="ck_board_media_ref_ready"),
        sa.PrimaryKeyConstraint("board_id", "slot"),
    )
    op.create_index("ix_board_media_refs_asset", "board_media_refs", ["asset_id"])


def downgrade() -> None:
    connection = op.get_bind()
    if (
        connection.scalar(sa.text("SELECT count(*) FROM board_media_assets"))
        or connection.scalar(sa.text("SELECT count(*) FROM board_media_refs"))
        or connection.scalar(
            sa.text(
                "SELECT count(*) FROM asset_deletion_outbox WHERE object_key LIKE 'board-media/%'"
            )
        )
    ):
        raise RuntimeError(
            "Board media or cleanup history remains; refusing destructive downgrade."
        )
    op.drop_table("board_media_refs")
    op.drop_table("board_media_assets")
