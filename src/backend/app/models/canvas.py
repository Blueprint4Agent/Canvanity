"""Canvas entities, API schemas and persistence; sessions never leave this module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Uuid,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import BoardTransaction, Shelf

MAX_CANVAS_REVISION = 2**63 - 1
CANVAS_TRASH_RETENTION_DAYS = 30
CANVAS_FIELDS = ("title", "summary", "shelf_id", "visibility")
CanvasStatus = Literal["draft", "trashed"]
CanvasVisibility = Literal["public", "members"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class Canvas(Base):
    __tablename__ = "canvases"
    __table_args__ = (
        Index("uq_canvas_board_id", "board_id", "id", unique=True),
        ForeignKeyConstraint(
            ["board_id", "shelf_id"],
            ["shelves.board_id", "shelves.id"],
            ondelete="RESTRICT",
            name="fk_canvas_shelf",
        ),
        CheckConstraint("status IN ('draft','trashed')", name="ck_canvas_status"),
        CheckConstraint("visibility IN ('public','members')", name="ck_canvas_visibility"),
        CheckConstraint("revision >= 0", name="ck_canvas_revision"),
        CheckConstraint(
            "(status = 'draft' AND trashed_at IS NULL) OR (status = 'trashed' AND trashed_at IS NOT NULL)",
            name="ck_canvas_trash_state",
        ),
        Index("ix_canvases_board_shelf", "board_id", "shelf_id"),
        Index("ix_canvases_author_id", "author_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="RESTRICT"))
    shelf_id: Mapped[UUID] = mapped_column(Uuid)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500), default="", server_default="")
    status: Mapped[str] = mapped_column(String(12), default="draft", server_default="draft")
    visibility: Mapped[str] = mapped_column(String(10), default="members", server_default="members")
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanvasDocument(Base):
    __tablename__ = "canvas_documents"
    __table_args__ = (CheckConstraint("revision >= 0", name="ck_canvas_document_revision"),)
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    document: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanvasEngine(BaseModel):
    name: Literal["excalidraw"] = "excalidraw"
    version: Literal["0.18.1"] = "0.18.1"
    adapter_version: Literal[1] = 1


class CanvasSettings(BaseModel):
    background: str = "#F8F7F4"
    grid: Literal["none", "dots"] = "dots"
    width: int = 3200
    height: int = 2100


class CanvasContent(BaseModel):
    schema_version: Literal[1] = 1
    engine: CanvasEngine = Field(default_factory=CanvasEngine)
    settings: CanvasSettings = Field(default_factory=CanvasSettings)
    # Creation only produces empty arrays. Element input validators belong to document saving (#7).
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    element_order: list[str] = Field(default_factory=list)


class CanvasCreateForm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    shelf_id: UUID
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    visibility: CanvasVisibility = "members"


class CanvasRevisionForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0, le=MAX_CANVAS_REVISION, strict=True)


def _patch_schema(schema: dict) -> None:
    for field in CANVAS_FIELDS:
        schema["properties"][field].pop("default", None)
    schema["allOf"] = [{"anyOf": [{"required": [field]} for field in CANVAS_FIELDS]}]


class CanvasPatchForm(CanvasRevisionForm):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, json_schema_extra=_patch_schema
    )
    title: str = Field(default=None, min_length=1, max_length=200)
    summary: str = Field(default=None, max_length=500)
    shelf_id: UUID = None
    visibility: CanvasVisibility = None

    @model_validator(mode="after")
    def at_least_one_change(self):
        if not self.model_fields_set.intersection(CANVAS_FIELDS):
            raise ValueError("Provide at least one canvas metadata field to change.")
        return self


class CanvasMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    board_id: UUID
    shelf_id: UUID
    author_id: int | None
    title: str
    summary: str
    visibility: CanvasVisibility
    status: CanvasStatus
    revision: int
    trashed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", "trashed_at")
    @classmethod
    def utc_datetimes(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None


class CanvasCapabilities(BaseModel):
    read_document: bool
    edit_metadata: bool
    trash: bool
    restore: bool


class CanvasResponse(BaseModel):
    canvas: CanvasMetadata
    document_revision: int
    view: Literal["draft"] = "draft"
    capabilities: CanvasCapabilities


class CanvasDocumentResponse(BaseModel):
    document: CanvasContent
    revision: int
    view: Literal["draft"] = "draft"


class CanvasTransaction:
    def __init__(self, db: AsyncSession):
        self._db = db
        self.board = BoardTransaction(db)

    async def board_id(self, canvas_id: UUID) -> UUID | None:
        return await self._db.scalar(select(Canvas.board_id).where(Canvas.id == canvas_id))

    async def canvas(self, canvas_id: UUID, *, locked: bool = False) -> Canvas | None:
        statement = select(Canvas).where(Canvas.id == canvas_id)
        return await self._db.scalar(statement.with_for_update() if locked else statement)

    async def document(self, canvas_id: UUID) -> CanvasDocument | None:
        return await self._db.get(CanvasDocument, canvas_id)

    async def shelf(self, board_id: UUID, shelf_id: UUID) -> Shelf | None:
        return await self._db.scalar(
            select(Shelf).where(Shelf.board_id == board_id, Shelf.id == shelf_id)
        )

    async def create(self, board_id: UUID, user_id: int, form: CanvasCreateForm) -> Canvas:
        canvas = Canvas(board_id=board_id, author_id=user_id, **form.model_dump())
        self._db.add(canvas)
        await self._db.flush()
        self._db.add(
            CanvasDocument(canvas_id=canvas.id, document=CanvasContent().model_dump(mode="json"))
        )
        await self._db.flush()
        return canvas

    async def patch(self, canvas: Canvas, form: CanvasPatchForm) -> None:
        changes = {
            key: getattr(form, key)
            for key in form.model_fields_set.intersection(CANVAS_FIELDS)
            if getattr(canvas, key) != getattr(form, key)
        }
        if not changes:
            return
        for key, value in changes.items():
            setattr(canvas, key, value)
        self._touch(canvas)
        await self._db.flush()

    @staticmethod
    def _touch(canvas: Canvas) -> None:
        if canvas.revision >= MAX_CANVAS_REVISION:
            raise CanvasException(CanvasErrorCode.CONFLICT, {"current_revision": canvas.revision})
        canvas.revision += 1
        canvas.updated_at = utc_now()

    async def trash(self, canvas: Canvas) -> None:
        if canvas.status == "trashed":
            return
        canvas.status = "trashed"
        canvas.trashed_at = utc_now()
        self._touch(canvas)
        await self._db.flush()

    async def restore(self, canvas: Canvas) -> None:
        if canvas.status == "draft":
            return
        canvas.status, canvas.trashed_at = "draft", None
        self._touch(canvas)
        await self._db.flush()


class CanvasRepository:
    @asynccontextmanager
    async def transaction(self, *, write: bool = True) -> AsyncIterator[CanvasTransaction]:
        try:
            async with get_db() as db:
                if write and db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                yield CanvasTransaction(db)
                if write:
                    await db.commit()
        except SQLAlchemyError as error:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE) from error
