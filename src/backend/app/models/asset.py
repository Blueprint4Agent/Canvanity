"""Canvas image persistence and durable, fenced file cleanup. No file I/O lives here."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
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
    and_,
    delete,
    func,
    or_,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.models.canvas import Canvas, CanvasTransaction, as_utc, utc_now
from app.models.user import User

MAX_ASSETS_PER_CANVAS = 200
PENDING_UPLOAD_SECONDS = 3600
UNUSED_ASSET_SECONDS = 86400
CLEANUP_LEASE_SECONDS = 600
CLEANUP_SETTLE_SECONDS = 60
MAX_CLEANUP_ATTEMPTS = 5
JOB_STATES = "'pending','processing','protected','blocked','dead','done'"


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["board_id", "canvas_id"],
            ["canvases.board_id", "canvases.id"],
            name="fk_asset_canvas",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("storage_fingerprint", "object_key", name="uq_asset_object"),
        UniqueConstraint("board_id", "canvas_id", "id", "state", name="uq_asset_ref_target"),
        CheckConstraint("state IN ('pending','ready','deleting')", name="ck_asset_state"),
        CheckConstraint(
            "byte_size > 0 AND width > 0 AND height > 0 AND frame_count > 0",
            name="ck_asset_dimensions",
        ),
        CheckConstraint(
            "content_type = 'image/webp' AND byte_size <= 8388608 AND frame_count <= 100 AND CAST(width AS BIGINT) * height * frame_count <= 16000000",
            name="ck_asset_bounds",
        ),
        Index("ix_assets_canvas", "board_id", "canvas_id", "state"),
        Index("ix_assets_owner", "owner_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="RESTRICT"))
    canvas_id: Mapped[UUID] = mapped_column(Uuid)
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
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanvasAssetRef(Base):
    __tablename__ = "canvas_asset_refs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["board_id", "canvas_id", "asset_id", "asset_state"],
            ["assets.board_id", "assets.canvas_id", "assets.id", "assets.state"],
            name="fk_canvas_asset_ref",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        CheckConstraint("scope IN ('draft','publication')", name="ck_asset_ref_scope"),
        CheckConstraint("asset_state = 'ready'", name="ck_asset_ref_ready"),
        Index("ix_asset_refs_asset", "asset_id"),
    )
    canvas_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    scope: Mapped[str] = mapped_column(String(12), primary_key=True)
    board_id: Mapped[UUID] = mapped_column(Uuid)
    asset_state: Mapped[str] = mapped_column(String(10), default="ready", server_default="ready")


class AssetDeletionOutbox(Base):
    __tablename__ = "asset_deletion_outbox"
    __table_args__ = (
        UniqueConstraint("storage_fingerprint", "object_key", name="uq_asset_cleanup_object"),
        CheckConstraint(f"state IN ({JOB_STATES})", name="ck_asset_cleanup_state"),
        CheckConstraint("attempts >= 0", name="ck_asset_cleanup_attempts"),
        Index("ix_asset_cleanup_due", "state", "available_at", "id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # Deliberately no parent FK: cleanup must outlive Board/Canvas/Asset deletion.
    asset_id: Mapped[UUID] = mapped_column(Uuid)
    board_id: Mapped[UUID] = mapped_column(Uuid)
    object_key: Mapped[str] = mapped_column(String(512))
    storage_fingerprint: Mapped[str] = mapped_column(String(64))
    storage_location: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    reason: Mapped[str] = mapped_column(String(24))
    state: Mapped[str] = mapped_column(String(12), default="pending", server_default="pending")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    lease_token: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    canvas_id: UUID
    content_type: Literal["image/webp"]
    byte_size: int
    width: int
    height: int
    frame_count: int
    state: Literal["ready"]
    expires_at: datetime | None
    created_at: datetime
    url: str


@dataclass(frozen=True)
class CleanupClaim:
    id: UUID
    asset_id: UUID
    token: UUID
    object_key: str
    fingerprint: str


class AssetTransaction:
    def __init__(self, db: AsyncSession):
        self._db = db
        self.context = CanvasTransaction(db)

    async def asset(self, asset_id: UUID, *, locked: bool = False) -> Asset | None:
        query = select(Asset).where(Asset.id == asset_id)
        return await self._db.scalar(query.with_for_update() if locked else query)

    async def has_refs(self, asset_id: UUID) -> bool:
        return (
            await self._db.scalar(
                select(CanvasAssetRef.asset_id).where(CanvasAssetRef.asset_id == asset_id).limit(1)
            )
            is not None
        )

    async def _job(self, asset: Asset) -> AssetDeletionOutbox | None:
        return await self._db.scalar(
            select(AssetDeletionOutbox)
            .where(
                AssetDeletionOutbox.storage_fingerprint == asset.storage_fingerprint,
                AssetDeletionOutbox.object_key == asset.object_key,
            )
            .with_for_update()
        )

    async def enqueue(self, asset: Asset, *, reason: str, available_at: datetime) -> None:
        job = await self._job(asset)
        if job is None:
            job = AssetDeletionOutbox(
                asset_id=asset.id,
                board_id=asset.board_id,
                object_key=asset.object_key,
                storage_fingerprint=asset.storage_fingerprint,
                storage_location=asset.storage_location,
                reason=reason,
                available_at=available_at,
            )
            self._db.add(job)
        else:
            job.reason, job.available_at, job.state = reason, available_at, "pending"
            job.attempts, job.lease_token, job.last_error = 0, None, None
        await self._db.flush()

    async def reserve(
        self,
        canvas: Canvas,
        user_id: int,
        *,
        asset_id: UUID,
        object_key: str,
        fingerprint: str,
        location: dict,
        byte_size: int,
        width: int,
        height: int,
        frame_count: int,
        sha256: str,
    ) -> Asset:
        count = await self._db.scalar(
            select(func.count()).select_from(Asset).where(Asset.canvas_id == canvas.id)
        )
        if count >= MAX_ASSETS_PER_CANVAS:
            raise AssetException(AssetErrorCode.LIMIT_REACHED)
        asset = Asset(
            id=asset_id,
            board_id=canvas.board_id,
            canvas_id=canvas.id,
            owner_id=user_id,
            object_key=object_key,
            storage_fingerprint=fingerprint,
            storage_location=location,
            byte_size=byte_size,
            width=width,
            height=height,
            frame_count=frame_count,
            sha256=sha256,
            upload_deadline=utc_now() + timedelta(seconds=PENDING_UPLOAD_SECONDS),
        )
        self._db.add(asset)
        await self._db.flush()
        await self.enqueue(asset, reason="upload_pending", available_at=asset.upload_deadline)
        return asset

    async def ready(self, asset: Asset) -> None:
        if asset.state != "pending" or as_utc(asset.upload_deadline) <= utc_now():
            raise AssetException(AssetErrorCode.CONFLICT)
        asset.state = "ready"
        asset.expires_at = utc_now() + timedelta(seconds=UNUSED_ASSET_SECONDS)
        await self._db.flush()
        await self.enqueue(asset, reason="unused_upload", available_at=asset.expires_at)

    async def request_delete(self, asset: Asset) -> None:
        if await self.has_refs(asset.id):
            raise AssetException(AssetErrorCode.REFERENCED)
        asset.state = "deleting"
        await self._db.flush()
        await self.enqueue(asset, reason="explicit_delete", available_at=utc_now())

    async def delete_board_assets(self, board_id: UUID) -> None:
        assets = list(
            (
                await self._db.scalars(
                    select(Asset)
                    .where(Asset.board_id == board_id)
                    .order_by(Asset.id)
                    .with_for_update()
                )
            ).all()
        )
        for asset in assets:
            when = (
                max(utc_now(), as_utc(asset.upload_deadline))
                if asset.state == "pending"
                else utc_now()
            )
            await self.enqueue(asset, reason="board_deleted", available_at=when)
        await self._db.execute(delete(CanvasAssetRef).where(CanvasAssetRef.board_id == board_id))
        await self._db.execute(delete(Asset).where(Asset.board_id == board_id))

    async def replace_refs(
        self, canvas: Canvas, asset_ids: set[UUID], *, scope: Literal["draft", "publication"]
    ) -> None:
        # Caller holds Board/Canvas locks and validates the actual document. This is not a public API.
        existing = set(
            (
                await self._db.scalars(
                    select(CanvasAssetRef.asset_id).where(
                        CanvasAssetRef.canvas_id == canvas.id, CanvasAssetRef.scope == scope
                    )
                )
            ).all()
        )
        affected = existing | asset_ids
        rows = (
            {
                a.id: a
                for a in (
                    await self._db.scalars(
                        select(Asset)
                        .where(Asset.id.in_(affected))
                        .order_by(Asset.id)
                        .with_for_update()
                    )
                ).all()
            }
            if affected
            else {}
        )
        if any(
            key not in rows
            or rows[key].state != "ready"
            or rows[key].canvas_id != canvas.id
            or rows[key].board_id != canvas.board_id
            for key in asset_ids
        ):
            raise AssetException(AssetErrorCode.INVALID_REFERENCE)
        await self._db.execute(
            delete(CanvasAssetRef).where(
                CanvasAssetRef.canvas_id == canvas.id, CanvasAssetRef.scope == scope
            )
        )
        self._db.add_all(
            [
                CanvasAssetRef(
                    board_id=canvas.board_id, canvas_id=canvas.id, asset_id=key, scope=scope
                )
                for key in asset_ids
            ]
        )
        await self._db.flush()
        for asset in rows.values():
            if await self.has_refs(asset.id):
                asset.expires_at = None
                job = await self._job(asset)
                if job:
                    job.state, job.lease_token, job.last_error = "protected", None, None
            else:
                asset.expires_at = utc_now() + timedelta(seconds=UNUSED_ASSET_SECONDS)
                await self.enqueue(asset, reason="unused_upload", available_at=asset.expires_at)
        await self._db.flush()

    async def job_context(self, job_id: UUID) -> tuple[Asset | None, AssetDeletionOutbox | None]:
        row = (
            await self._db.execute(
                select(AssetDeletionOutbox.board_id, AssetDeletionOutbox.asset_id).where(
                    AssetDeletionOutbox.id == job_id
                )
            )
        ).first()
        if row is None:
            return None, None
        await self.context.board.locked_board(row.board_id)
        asset = await self.asset(row.asset_id, locked=True)
        job = await self._db.scalar(
            select(AssetDeletionOutbox)
            .where(AssetDeletionOutbox.id == job_id)
            .with_for_update(skip_locked=True)
        )
        return asset, job

    async def key_live(self, job: AssetDeletionOutbox) -> bool:
        other = await self._db.scalar(
            select(Asset.id)
            .where(
                Asset.storage_fingerprint == job.storage_fingerprint,
                Asset.object_key == job.object_key,
                Asset.id != job.asset_id,
            )
            .limit(1)
        )
        if other is not None or await self.has_refs(job.asset_id):
            return True
        # Profile references predate the asset registry and deliberately remain separate.
        return (
            await self._db.scalar(
                select(User.id)
                .where(
                    User.profile_photo["key"].as_string() == job.object_key,
                    User.profile_photo["storage"].as_string() == job.storage_fingerprint,
                )
                .limit(1)
            )
            is not None
        )


class AssetRepository:
    @asynccontextmanager
    async def transaction(self, *, write: bool = True) -> AsyncIterator[AssetTransaction]:
        try:
            async with get_db() as db:
                if write and db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                yield AssetTransaction(db)
                if write:
                    await db.commit()
        except SQLAlchemyError as error:
            raise AssetException(AssetErrorCode.UNAVAILABLE) from error

    async def upload_failed(self, asset_id: UUID) -> None:
        async with self.transaction() as tx:
            initial = (
                await tx._db.execute(
                    select(AssetDeletionOutbox.id).where(AssetDeletionOutbox.asset_id == asset_id)
                )
            ).scalar_one_or_none()
            if initial is None:
                return
            asset, job = await tx.job_context(initial)
            if job is None or (asset is not None and asset.state == "ready"):
                return  # Ambiguous commit: never compensate a confirmed ready upload.
            if asset is not None:
                asset.state = "deleting"
            job.state, job.reason = "pending", "upload_failed"
            job.available_at = max(
                utc_now() + timedelta(seconds=CLEANUP_SETTLE_SECONDS),
                as_utc(asset.upload_deadline) if asset is not None else as_utc(job.available_at),
            )
            job.attempts, job.lease_token, job.last_error = 0, None, None

    async def due(self, *, limit: int) -> list[UUID]:
        async with self.transaction(write=False) as tx:
            return list(
                (
                    await tx._db.scalars(
                        select(AssetDeletionOutbox.id)
                        .where(
                            AssetDeletionOutbox.state.in_(["pending", "processing"]),
                            AssetDeletionOutbox.available_at <= utc_now(),
                        )
                        .order_by(AssetDeletionOutbox.available_at, AssetDeletionOutbox.id)
                        .limit(limit)
                    )
                ).all()
            )

    async def claim(self, job_id: UUID, fingerprint: str) -> CleanupClaim | None:
        async with self.transaction() as tx:
            asset, job = await tx.job_context(job_id)
            if (
                job is None
                or job.state not in {"pending", "processing"}
                or as_utc(job.available_at) > utc_now()
            ):
                return None
            if job.storage_fingerprint != fingerprint:
                job.state, job.last_error = "blocked", "storage_mismatch"
                return None
            if (
                asset is not None
                and asset.state == "pending"
                and as_utc(asset.upload_deadline) > utc_now()
            ):
                job.available_at = asset.upload_deadline
                return None
            if await tx.key_live(job):
                job.state, job.last_error = "protected", "live_reference"
                return None
            if job.attempts >= MAX_CLEANUP_ATTEMPTS:
                job.state, job.last_error, job.lease_token = "dead", "lease_expired", None
                return None
            if asset is not None:
                asset.state = "deleting"
                await tx._db.flush()
            job.state, job.lease_token = "processing", uuid4()
            job.attempts += 1
            job.available_at = utc_now() + timedelta(seconds=CLEANUP_LEASE_SECONDS)
            result = CleanupClaim(
                job.id, job.asset_id, job.lease_token, job.object_key, job.storage_fingerprint
            )
        return result

    async def finish(self, claim: CleanupClaim, *, error: str | None = None) -> bool:
        async with self.transaction() as tx:
            asset, job = await tx.job_context(claim.id)
            if job is None or job.state != "processing" or job.lease_token != claim.token:
                return False
            if error is None:
                if asset is not None:
                    await tx._db.delete(asset)
                job.state, job.last_error = "done", None
            else:
                job.state = (
                    "blocked"
                    if error in {"invalid_key", "storage_mismatch"}
                    else "dead"
                    if job.attempts >= MAX_CLEANUP_ATTEMPTS
                    else "pending"
                )
                job.last_error = error
                job.available_at = utc_now() + timedelta(
                    seconds=min(3600, 60 * 2 ** min(job.attempts - 1, 6))
                )
            job.lease_token = None
        return True

    async def retry(self, job_id: UUID) -> bool:
        async with self.transaction() as tx:
            _, job = await tx.job_context(job_id)
            if job is None or (job.state == "processing" and as_utc(job.available_at) > utc_now()):
                return False
            job.state, job.attempts, job.lease_token, job.last_error = "pending", 0, None, None
            job.available_at = utc_now()
        return True

    async def inventory(self, *, limit: int = 50) -> list[dict]:
        async with self.transaction(write=False) as tx:
            jobs = (
                await tx._db.scalars(
                    select(AssetDeletionOutbox)
                    .where(
                        or_(
                            AssetDeletionOutbox.state.in_(["blocked", "dead", "processing"]),
                            and_(
                                AssetDeletionOutbox.state == "protected",
                                AssetDeletionOutbox.last_error.is_not(None),
                            ),
                        )
                    )
                    .order_by(AssetDeletionOutbox.available_at, AssetDeletionOutbox.id)
                    .limit(limit)
                )
            ).all()
            return [
                {
                    "id": str(j.id),
                    "state": j.state,
                    "attempts": j.attempts,
                    "last_error": j.last_error,
                    "fingerprint": j.storage_fingerprint,
                    "reason": j.reason,
                }
                for j in jobs
            ]
