"""Canvas image registry, ready references and parent-independent cleanup."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0027_canvas_assets"
down_revision = "0026_canvas_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A unique index avoids rebuilding populated SQLite Canvas tables (and cascading documents).
    op.create_index("uq_canvas_board_id", "canvases", ["board_id", "id"], unique=True)
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["board_id", "canvas_id"],
            ["canvases.board_id", "canvases.id"],
            name="fk_asset_canvas",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("storage_fingerprint", "object_key", name="uq_asset_object"),
        sa.UniqueConstraint("board_id", "canvas_id", "id", "state", name="uq_asset_ref_target"),
        sa.CheckConstraint("state IN ('pending','ready','deleting')", name="ck_asset_state"),
        sa.CheckConstraint(
            "byte_size > 0 AND width > 0 AND height > 0 AND frame_count > 0",
            name="ck_asset_dimensions",
        ),
        sa.CheckConstraint(
            "content_type = 'image/webp' AND byte_size <= 8388608 AND frame_count <= 100 AND CAST(width AS BIGINT) * height * frame_count <= 16000000",
            name="ck_asset_bounds",
        ),
    )
    op.create_index("ix_assets_canvas", "assets", ["board_id", "canvas_id", "state"])
    op.create_index("ix_assets_owner", "assets", ["owner_id"])
    op.create_table(
        "canvas_asset_refs",
        sa.Column("canvas_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(12), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("asset_state", sa.String(10), server_default="ready", nullable=False),
        sa.PrimaryKeyConstraint("canvas_id", "asset_id", "scope"),
        sa.ForeignKeyConstraint(
            ["board_id", "canvas_id", "asset_id", "asset_state"],
            ["assets.board_id", "assets.canvas_id", "assets.id", "assets.state"],
            name="fk_canvas_asset_ref",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("scope IN ('draft','publication')", name="ck_asset_ref_scope"),
        sa.CheckConstraint("asset_state = 'ready'", name="ck_asset_ref_ready"),
    )
    op.create_index("ix_asset_refs_asset", "canvas_asset_refs", ["asset_id"])
    op.create_table(
        "asset_deletion_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("board_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("storage_fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "storage_location",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(24), nullable=False),
        sa.Column("state", sa.String(12), server_default="pending", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("last_error", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_fingerprint", "object_key", name="uq_asset_cleanup_object"),
        sa.CheckConstraint(
            "state IN ('pending','processing','protected','blocked','dead','done')",
            name="ck_asset_cleanup_state",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_asset_cleanup_attempts"),
    )
    op.create_index(
        "ix_asset_cleanup_due", "asset_deletion_outbox", ["state", "available_at", "id"]
    )


def downgrade() -> None:
    # A downgrade must not silently drop the only durable cleanup record for real files.
    connection = op.get_bind()
    if (
        connection.execute(sa.text("SELECT count(*) FROM assets")).scalar()
        or connection.execute(
            sa.text("SELECT count(*) FROM asset_deletion_outbox WHERE state != 'done'")
        ).scalar()
    ):
        raise RuntimeError("Drain asset cleanup and remove asset references before downgrading.")
    op.drop_table("canvas_asset_refs")
    op.drop_table("asset_deletion_outbox")
    op.drop_table("assets")
    op.drop_index("uq_canvas_board_id", table_name="canvases")
