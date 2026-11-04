"""Owner-only Canvas headers and bounded batch reads in a repository-owned snapshot."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import and_, case, exists, func, or_, select, text, true
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only

from app.core.db.session import get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import Board, BoardMember, BoardMemberGrade, BoardPolicy, Shelf, ShelfPolicy
from app.models.canvas import (
    Canvas,
    CanvasDocument,
    CanvasPublication,
    CanvasPublicationCounter,
    CanvasPublicationInfo,
    CanvasResponse,
    as_utc,
)
from app.models.tag import CanvasTag, Tag, TagResponse
from app.models.user import User


class CanvasListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["draft", "trashed", "all"] = "draft"
    publication: Literal["all", "published", "unpublished"] = "all"
    board_id: UUID | None = None
    shelf_id: UUID | None = None
    sort: Literal["last_modified"] = "last_modified"
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, min_length=1, max_length=2048)


class CanvasListItem(CanvasResponse):
    document_updated_at: datetime
    last_modified_at: datetime
    trash_expires_at: datetime | None
    trash_expired: bool


class CanvasListResponse(BaseModel):
    items: list[CanvasListItem]
    as_of: datetime
    next_cursor: str | None = None


class CanvasListCursor(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    v: int
    domain: Literal["canvas-owner-list"]
    user_id: int = Field(gt=0)
    sort: Literal["last_modified"]
    filter_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    last_modified_at: datetime
    canvas_id: UUID

    @field_validator("v")
    @classmethod
    def version_one(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Unsupported cursor version.")
        return value

    @field_validator("last_modified_at", mode="before")
    @classmethod
    def utc_timestamp(cls, value: object) -> object:
        if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value
        ):
            raise ValueError("Cursor timestamp must be an explicit UTC RFC3339 string.")
        return datetime.fromisoformat(value)


@dataclass(frozen=True)
class CanvasListRow:
    canvas: Canvas
    board: Board
    member: BoardMember
    document_revision: int
    document_updated_at: datetime
    last_modified_at: datetime
    publication_revision: int
    publication: CanvasPublicationInfo | None


@dataclass
class CanvasListScope:
    board: Board
    member: BoardMember
    shelf_id: UUID
    has_own: bool


@dataclass
class CanvasListData:
    account_active: bool
    scope_readable: bool
    scope: CanvasListScope | None = None
    rows: list[CanvasListRow] = field(default_factory=list)
    grades: dict[UUID, BoardMemberGrade] = field(default_factory=dict)
    policies: dict[UUID, dict[str, BoardPolicy]] = field(default_factory=dict)
    overrides: dict[tuple[UUID, str], ShelfPolicy] = field(default_factory=dict)
    tags: dict[UUID, list[TagResponse]] = field(default_factory=dict)


class CanvasListRepository:
    async def read(
        self, user_id: int, query: CanvasListQuery, before: tuple[datetime, UUID] | None
    ) -> CanvasListData:
        # Own-draft read deliberately ignores Shelf read grade, like read_context(view=draft).
        boards = (
            select(Board.id.label("board_id"))
            .join(BoardMember, BoardMember.board_id == Board.id)
            .where(
                Board.status.in_(("active", "archived")),
                BoardMember.user_id == user_id,
                BoardMember.status == "active",
                Board.id == query.board_id if query.board_id is not None else true(),
            )
            .cte("owner_boards")
        )
        scope = true()
        if query.shelf_id is not None:
            scope = (
                select(Shelf.id)
                .join(boards, boards.c.board_id == Shelf.board_id)
                .where(Shelf.id == query.shelf_id)
                .exists()
            )
        elif query.board_id is not None:
            scope = select(boards.c.board_id).exists()
        flags = select(exists().where(User.id == user_id, User.is_active.is_(True)), scope)
        modified = case(
            (CanvasDocument.updated_at > Canvas.updated_at, CanvasDocument.updated_at),
            else_=Canvas.updated_at,
        )
        statement = (
            select(
                Canvas,
                Board,
                BoardMember,
                CanvasDocument.revision.label("document_revision"),
                CanvasDocument.updated_at.label("document_updated_at"),
                modified.label("last_modified_at"),
                func.coalesce(CanvasPublicationCounter.revision, 0).label("state_revision"),
                CanvasPublication.publication_revision,
                CanvasPublication.source_metadata_revision,
                CanvasPublication.source_document_revision,
                CanvasPublication.published_at,
            )
            .join(boards, boards.c.board_id == Canvas.board_id)
            .join(Board, Board.id == Canvas.board_id)
            .join(
                BoardMember,
                and_(BoardMember.board_id == Board.id, BoardMember.user_id == user_id),
            )
            .outerjoin(CanvasDocument, CanvasDocument.canvas_id == Canvas.id)
            .outerjoin(CanvasPublication, CanvasPublication.canvas_id == Canvas.id)
            .outerjoin(CanvasPublicationCounter, CanvasPublicationCounter.canvas_id == Canvas.id)
            .options(load_only(Board.id, Board.status, Board.visibility))
            .where(Canvas.author_id == user_id)
        )
        if query.shelf_id is not None:
            statement = statement.where(Canvas.shelf_id == query.shelf_id)
        if query.status != "all":
            statement = statement.where(Canvas.status == query.status)
        if query.publication != "all":
            published = CanvasPublication.canvas_id.is_not(None)
            statement = statement.where(
                published if query.publication == "published" else ~published
            )
        if before is not None:
            timestamp, canvas_id = before
            statement = statement.where(
                or_(modified < timestamp, and_(modified == timestamp, Canvas.id < canvas_id))
            )
        statement = statement.order_by(modified.desc(), Canvas.id.desc()).limit(query.limit + 1)
        try:
            async with get_db() as db:
                await db.execute(
                    text(
                        "BEGIN"
                        if db.bind.dialect.name == "sqlite"
                        else "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                    )
                )
                account, readable = (await db.execute(flags)).one()
                data = CanvasListData(bool(account), bool(readable))
                if not account or not readable:
                    return data
                if query.shelf_id is not None:
                    # Scope existence alone must not disclose an unreadable, unowned Shelf.
                    # Own presence ignores page/status/publication filters, like draft read.
                    scope_row = (
                        await db.execute(
                            select(
                                Board,
                                BoardMember,
                                exists().where(
                                    Canvas.author_id == user_id,
                                    Canvas.shelf_id == query.shelf_id,
                                    Canvas.board_id == Board.id,
                                ),
                            )
                            .join(boards, boards.c.board_id == Board.id)
                            .join(
                                BoardMember,
                                and_(
                                    BoardMember.board_id == Board.id,
                                    BoardMember.user_id == user_id,
                                ),
                            )
                            .join(Shelf, Shelf.board_id == Board.id)
                            .where(Shelf.id == query.shelf_id)
                            .options(load_only(Board.id, Board.status, Board.visibility))
                        )
                    ).one()
                    data.scope = CanvasListScope(
                        scope_row.Board, scope_row.BoardMember, query.shelf_id, bool(scope_row[2])
                    )
                rows = (await db.execute(statement)).all()
                for row in rows:
                    if row.document_revision is None or row.document_updated_at is None:
                        raise CanvasException(CanvasErrorCode.UNAVAILABLE)
                    data.rows.append(
                        CanvasListRow(
                            row.Canvas,
                            row.Board,
                            row.BoardMember,
                            row.document_revision,
                            as_utc(row.document_updated_at),
                            as_utc(row.last_modified_at),
                            row.state_revision,
                            CanvasPublicationInfo(
                                publication_revision=row.publication_revision,
                                source_metadata_revision=row.source_metadata_revision,
                                source_document_revision=row.source_document_revision,
                                published_at=row.published_at,
                            )
                            if row.publication_revision is not None
                            else None,
                        )
                    )
                if not rows and data.scope is None:
                    return data
                board_ids = {row.canvas.board_id for row in data.rows}
                shelf_ids = {row.canvas.shelf_id for row in data.rows}
                if data.scope is not None:
                    board_ids.add(data.scope.board.id)
                    shelf_ids.add(data.scope.shelf_id)
                canvas_ids = [row.canvas.id for row in data.rows]
                data.grades = {
                    grade.id: grade
                    for grade in await db.scalars(
                        select(BoardMemberGrade).where(BoardMemberGrade.board_id.in_(board_ids))
                    )
                }
                for policy in await db.scalars(
                    select(BoardPolicy).where(BoardPolicy.board_id.in_(board_ids))
                ):
                    data.policies.setdefault(policy.board_id, {})[policy.action] = policy
                data.overrides = {
                    (policy.shelf_id, policy.action): policy
                    for policy in await db.scalars(
                        select(ShelfPolicy).where(
                            ShelfPolicy.board_id.in_(board_ids), ShelfPolicy.shelf_id.in_(shelf_ids)
                        )
                    )
                }
                if canvas_ids:
                    tags = await db.execute(
                        select(CanvasTag.canvas_id, Tag.id, Tag.name)
                        .join(Tag, Tag.id == CanvasTag.tag_id)
                        .where(CanvasTag.canvas_id.in_(canvas_ids))
                        .order_by(Tag.normalized_name, Tag.id)
                    )
                    for canvas_id, tag_id, name in tags:
                        data.tags.setdefault(canvas_id, []).append(
                            TagResponse(id=tag_id, name=name)
                        )
                return data
        except SQLAlchemyError as error:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE) from error
