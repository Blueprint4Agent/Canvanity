"""Board-owned images, ready slot references and atomic selection persistence."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    delete,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.utils.form_fields import MAX_INT32, AuditReason

if TYPE_CHECKING:
    from app.models.board import Board

MAX_BOARD_REVISION = MAX_INT32
MAX_BOARD_MEDIA_ASSETS = 200
MAX_PENDING_BOARD_MEDIA = 8


class BoardMediaSlot(StrEnum):
    AVATAR = "avatar"
    COVER = "cover"


def now() -> datetime:
    return datetime.now(UTC)


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class BoardMediaAsset(Base):
    __tablename__ = "board_media_assets"
    __table_args__ = (
        UniqueConstraint("storage_fingerprint", "object_key", name="uq_board_media_object"),
        UniqueConstraint("board_id", "slot", "id", "state", name="uq_board_media_ref_target"),
        CheckConstraint("slot IN ('avatar','cover')", name="ck_board_media_slot"),
        CheckConstraint("state IN ('pending','ready','deleting')", name="ck_board_media_state"),
        CheckConstraint(
            "byte_size > 0 AND width > 0 AND height > 0 AND frame_count > 0",
            name="ck_board_media_dimensions",
        ),
        CheckConstraint(
            "content_type = 'image/webp' AND byte_size <= 8388608 AND frame_count <= 100 AND CAST(width AS BIGINT) * height * frame_count <= 16000000",
            name="ck_board_media_bounds",
        ),
        Index("ix_board_media_owner", "owner_id"),
        Index("ix_board_media_board_state", "board_id", "state"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="RESTRICT"))
    slot: Mapped[str] = mapped_column(String(6))
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    object_key: Mapped[str] = mapped_column(String(512))
    storage_fingerprint: Mapped[str] = mapped_column(String(64))
    storage_location: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    content_type: Mapped[str] = mapped_column(
        String(50), default="image/webp", server_default="image/webp"
    )
    byte_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    frame_count: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(10), default="pending", server_default="pending")
    upload_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BoardMediaRef(Base):
    __tablename__ = "board_media_refs"
    __table_args__ = (
        ForeignKeyConstraint(
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
        CheckConstraint("slot IN ('avatar','cover')", name="ck_board_media_ref_slot"),
        CheckConstraint("asset_state = 'ready'", name="ck_board_media_ref_ready"),
        Index("ix_board_media_refs_asset", "asset_id"),
    )
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="RESTRICT"), primary_key=True
    )
    slot: Mapped[str] = mapped_column(String(6), primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(Uuid)
    asset_state: Mapped[str] = mapped_column(String(10), default="ready", server_default="ready")


class BoardMediaSummary(BaseModel):
    id: UUID
    content_type: Literal["image/webp"]
    byte_size: int
    width: int
    height: int
    frame_count: int
    created_at: datetime
    url: str

    @classmethod
    def from_asset(cls, asset: BoardMediaAsset) -> "BoardMediaSummary":
        return cls(
            id=asset.id,
            content_type=asset.content_type,
            byte_size=asset.byte_size,
            width=asset.width,
            height=asset.height,
            frame_count=asset.frame_count,
            created_at=utc(asset.created_at),
            url=f"/api/v1/boards/{asset.board_id}/media/{asset.slot}/{asset.id}",
        )


class BoardMediaChangeForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0, le=MAX_BOARD_REVISION, strict=True)
    reason: AuditReason


class BoardMediaMultipartError(BaseModel):
    detail: str


class BoardMediaUpdateResponse(BaseModel):
    board_id: UUID
    slot: BoardMediaSlot
    media: BoardMediaSummary | None
    board_revision: int
    changed: bool


class BoardMediaAuditChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot: BoardMediaSlot
    before_asset_id: UUID | None
    after_asset_id: UUID | None
    before_revision: int
    after_revision: int


class BoardMediaTransaction:
    def __init__(self, db: AsyncSession):
        from app.models.board import BoardTransaction

        self._db = db
        self.board = BoardTransaction(db)

    async def account_active(self, user_id: int) -> bool:
        from app.models.user import User

        return (
            await self._db.scalar(
                select(User.id).where(User.id == user_id, User.is_active.is_(True))
            )
            is not None
        )

    async def current_batch(
        self, board_ids: list[UUID]
    ) -> dict[UUID, dict[str, BoardMediaSummary]]:
        rows = (
            await self._db.scalars(
                select(BoardMediaAsset)
                .join(
                    BoardMediaRef,
                    (BoardMediaRef.board_id == BoardMediaAsset.board_id)
                    & (BoardMediaRef.slot == BoardMediaAsset.slot)
                    & (BoardMediaRef.asset_id == BoardMediaAsset.id)
                    & (BoardMediaRef.asset_state == BoardMediaAsset.state),
                )
                .where(BoardMediaRef.board_id.in_(board_ids), BoardMediaAsset.state == "ready")
            )
        ).all()
        result = {key: {} for key in board_ids}
        for row in rows:
            result[row.board_id][row.slot] = BoardMediaSummary.from_asset(row)
        return result

    async def current(
        self, board_id: UUID, slot: BoardMediaSlot, asset_id: UUID
    ) -> BoardMediaAsset | None:
        return await self._db.scalar(
            select(BoardMediaAsset)
            .join(
                BoardMediaRef,
                (BoardMediaRef.board_id == BoardMediaAsset.board_id)
                & (BoardMediaRef.slot == BoardMediaAsset.slot)
                & (BoardMediaRef.asset_id == BoardMediaAsset.id)
                & (BoardMediaRef.asset_state == BoardMediaAsset.state),
            )
            .where(
                BoardMediaAsset.id == asset_id,
                BoardMediaAsset.board_id == board_id,
                BoardMediaAsset.slot == slot,
                BoardMediaAsset.state == "ready",
            )
        )

    async def reserve(self, board: "Board", user_id: int, **values) -> BoardMediaAsset:
        from app.models.asset import PENDING_UPLOAD_SECONDS, AssetTransaction

        total = await self._db.scalar(
            select(func.count())
            .select_from(BoardMediaAsset)
            .where(BoardMediaAsset.board_id == board.id)
        )
        pending = await self._db.scalar(
            select(func.count())
            .select_from(BoardMediaAsset)
            .where(BoardMediaAsset.board_id == board.id, BoardMediaAsset.state == "pending")
        )
        if total >= MAX_BOARD_MEDIA_ASSETS or pending >= MAX_PENDING_BOARD_MEDIA:
            raise BoardException(BoardErrorCode.MEDIA_LIMIT_REACHED)
        asset = BoardMediaAsset(
            board_id=board.id,
            owner_id=user_id,
            upload_deadline=now() + timedelta(seconds=PENDING_UPLOAD_SECONDS),
            **values,
        )
        self._db.add(asset)
        await self._db.flush()
        await AssetTransaction(self._db).enqueue(
            asset, reason="upload_pending", available_at=asset.upload_deadline
        )
        return asset

    async def select(
        self,
        board: "Board",
        actor_id: int,
        slot: BoardMediaSlot,
        asset_id: UUID | None,
        reason: str,
    ) -> BoardMediaUpdateResponse:
        from app.models.asset import AssetTransaction
        from app.models.board import BoardMemberAudit

        reference = await self._db.get(BoardMediaRef, (board.id, slot))
        old_id = reference.asset_id if reference else None
        affected = {key for key in (old_id, asset_id) if key is not None}
        rows = (
            {
                row.id: row
                for row in (
                    await self._db.scalars(
                        select(BoardMediaAsset)
                        .where(
                            BoardMediaAsset.id.in_(affected),
                            BoardMediaAsset.board_id == board.id,
                            BoardMediaAsset.slot == slot,
                        )
                        .order_by(BoardMediaAsset.id)
                        .with_for_update()
                    )
                ).all()
            }
            if affected
            else {}
        )
        if asset_id is not None and (
            asset_id not in rows
            or rows[asset_id].state != "pending"
            or utc(rows[asset_id].upload_deadline) <= now()
        ):
            raise BoardException(BoardErrorCode.MEDIA_CONFLICT)
        if old_id is None and asset_id is None:
            return BoardMediaUpdateResponse(
                board_id=board.id,
                slot=slot,
                media=None,
                board_revision=board.revision,
                changed=False,
            )
        if board.revision >= MAX_BOARD_REVISION:
            raise BoardException(BoardErrorCode.REVISION_EXHAUSTED)
        # Flush the ref removal before changing its RESTRICT FK target's state.
        if reference is not None:
            await self._db.delete(reference)
            await self._db.flush()
        cleanup = AssetTransaction(self._db)
        if old_id is not None:
            old = rows[old_id]
            old.state = "deleting"
            await self._db.flush()
            await cleanup.enqueue(
                old, reason="media_replaced" if asset_id else "media_removed", available_at=now()
            )
        summary = None
        if asset_id is not None:
            asset = rows[asset_id]
            asset.state = "ready"
            await self._db.flush()
            self._db.add(BoardMediaRef(board_id=board.id, slot=slot, asset_id=asset.id))
            await self._db.flush()
            await cleanup.protect(asset)
            summary = BoardMediaSummary.from_asset(asset)
        before_revision = board.revision
        board.revision += 1
        board.updated_at = now()
        change = BoardMediaAuditChange(
            slot=slot,
            before_asset_id=old_id,
            after_asset_id=asset_id,
            before_revision=before_revision,
            after_revision=board.revision,
        )
        self._db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=actor_id,
                action="media_changed",
                changes={**change.model_dump(mode="json"), "reason": reason},
            )
        )
        await self._db.flush()
        return BoardMediaUpdateResponse(
            board_id=board.id, slot=slot, media=summary, board_revision=board.revision, changed=True
        )

    async def delete_board_media(self, board_id: UUID) -> None:
        from app.models.asset import AssetTransaction

        assets = (
            await self._db.scalars(
                select(BoardMediaAsset)
                .where(BoardMediaAsset.board_id == board_id)
                .order_by(BoardMediaAsset.id)
                .with_for_update()
            )
        ).all()
        cleanup = AssetTransaction(self._db)
        for asset in assets:
            await cleanup.enqueue(
                asset,
                reason="board_deleted",
                available_at=max(now(), utc(asset.upload_deadline))
                if asset.state == "pending"
                else now(),
                preserve_upload_grace=True,
            )
        await self._db.execute(delete(BoardMediaRef).where(BoardMediaRef.board_id == board_id))
        await self._db.execute(delete(BoardMediaAsset).where(BoardMediaAsset.board_id == board_id))


class BoardMediaRepository:
    @asynccontextmanager
    async def transaction(self, *, write: bool = True) -> AsyncIterator[BoardMediaTransaction]:
        try:
            async with get_db() as db:
                if db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE" if write else "BEGIN"))
                elif not write:
                    await db.execute(
                        text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    )
                yield BoardMediaTransaction(db)
                if write:
                    await db.commit()
        except SQLAlchemyError as error:
            raise BoardException(BoardErrorCode.UNAVAILABLE) from error

    async def upload_failed(self, asset_id: UUID) -> None:
        from app.models.asset import AssetRepository

        await AssetRepository().upload_failed(asset_id, namespace="board-media")
