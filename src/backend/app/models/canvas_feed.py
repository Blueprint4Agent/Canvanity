"""Publication-only feed DTOs and statement-consistent, metadata-only SQL reads."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import and_, case, exists, false, func, or_, select, true
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from app.core.db.session import get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import (
    BOARD_STAFF_ROLES,
    Board,
    BoardInterest,
    BoardMember,
    BoardMemberGrade,
    BoardPolicy,
    Shelf,
    ShelfPolicy,
)
from app.models.canvas import (
    Canvas,
    CanvasPublication,
    CanvasPublicationInfo,
    CanvasPublicationMetadata,
    CanvasPublicationTag,
    as_utc,
)
from app.models.interest import Interest
from app.models.tag import TagResponse
from app.models.user import User


class CanvasFeedFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=20, ge=1, le=100)
    sort: Literal["latest"] = "latest"
    interest_id: str | None = Field(
        default=None, min_length=2, max_length=40, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    tag_id: UUID | None = None
    cursor: str | None = Field(default=None, min_length=1, max_length=2048)


class CanvasFeedQuery(CanvasFeedFilters):
    board_id: UUID | None = None
    shelf_id: UUID | None = None


class CanvasFeedLocation(BaseModel):
    id: UUID
    slug: str
    name: str


class CanvasFeedItem(CanvasPublicationInfo):
    canvas: CanvasPublicationMetadata
    board: CanvasFeedLocation
    shelf: CanvasFeedLocation
    view: Literal["publication"] = "publication"


class CanvasFeedResponse(BaseModel):
    items: list[CanvasFeedItem]
    next_cursor: str | None = None


class CanvasFeedCursor(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    v: int
    domain: Literal["canvas-publication-feed"]
    scope: str = Field(min_length=1, max_length=80)
    sort: Literal["latest"]
    filter_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    published_at: datetime
    canvas_id: UUID

    @field_validator("v")
    @classmethod
    def version_one(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Unsupported cursor version.")
        return value

    @field_validator("published_at", mode="before")
    @classmethod
    def utc_timestamp(cls, value: object) -> object:
        if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value
        ):
            raise ValueError("Cursor timestamp must be an explicit UTC RFC3339 string.")
        return datetime.fromisoformat(value)


@dataclass(frozen=True)
class CanvasFeedRows:
    account_active: bool
    scope_readable: bool
    items: list[CanvasFeedItem]


class CanvasFeedRepository:
    @staticmethod
    def _readable_boards(user_id: int | None, board_id: UUID | None):
        active = func.coalesce(BoardMember.status == "active", false())
        return (
            select(
                Board.id.label("board_id"),
                Board.slug.label("board_slug"),
                Board.name.label("board_name"),
                active.label("active_member"),
                BoardMember.role.label("member_role"),
                BoardMember.grade_id.label("member_grade_id"),
            )
            .outerjoin(
                BoardMember,
                and_(BoardMember.board_id == Board.id, BoardMember.user_id == user_id),
            )
            .where(
                Board.status.in_(("active", "archived")),
                or_(
                    BoardMember.status.is_(None), BoardMember.status.not_in(("banned", "suspended"))
                ),
                or_(Board.visibility == "public", active),
                Board.id == board_id if board_id is not None else true(),
            )
            .cte("readable_boards")
        )

    @staticmethod
    def _readable_shelves(boards, shelf_id: UUID | None):
        """SQL equivalent of BoardPermissionService.allowed(..., 'read_canvas')."""
        own, minimum = aliased(BoardMemberGrade), aliased(BoardMemberGrade)
        override = ShelfPolicy.shelf_id.is_not(None)

        def effective(name):
            return case((override, getattr(ShelfPolicy, name)), else_=getattr(BoardPolicy, name))

        staff = boards.c.member_role.in_(tuple(sorted(BOARD_STAFF_ROLES)))
        policy_read = or_(
            effective("audience") == "public",
            and_(
                boards.c.active_member,
                or_(
                    and_(effective("staff_only"), staff),
                    and_(
                        ~effective("staff_only"),
                        or_(and_(staff, effective("staff_bypass")), own.rank >= minimum.rank),
                    ),
                ),
            ),
        )
        return (
            select(
                boards,
                Shelf.id.label("shelf_id"),
                Shelf.slug.label("shelf_slug"),
                Shelf.name.label("shelf_name"),
            )
            .join(Shelf, Shelf.board_id == boards.c.board_id)
            .outerjoin(
                BoardPolicy,
                and_(
                    BoardPolicy.board_id == boards.c.board_id, BoardPolicy.action == "read_canvas"
                ),
            )
            .outerjoin(
                ShelfPolicy,
                and_(
                    ShelfPolicy.board_id == boards.c.board_id,
                    ShelfPolicy.shelf_id == Shelf.id,
                    ShelfPolicy.action == "read_canvas",
                ),
            )
            .outerjoin(
                own,
                and_(own.board_id == boards.c.board_id, own.id == boards.c.member_grade_id),
            )
            .outerjoin(
                minimum,
                and_(
                    minimum.board_id == boards.c.board_id, minimum.id == effective("min_grade_id")
                ),
            )
            .where(policy_read, Shelf.id == shelf_id if shelf_id is not None else true())
            .cte("readable_shelves")
        )

    async def read(
        self,
        user_id: int | None,
        query: CanvasFeedQuery,
        before: tuple[datetime, UUID] | None,
    ) -> CanvasFeedRows:
        boards = self._readable_boards(user_id, query.board_id)
        shelves = self._readable_shelves(boards, query.shelf_id)
        scope = true()
        if query.shelf_id is not None:
            target = select(shelves.c.shelf_id).where(shelves.c.shelf_id == query.shelf_id)
            if query.board_id is not None:
                target = target.where(shelves.c.board_id == query.board_id)
            scope = target.exists()
        elif query.board_id is not None:
            scope = select(boards.c.board_id).where(boards.c.board_id == query.board_id).exists()
        account = (
            exists().where(User.id == user_id, User.is_active.is_(True))
            if user_id is not None
            else true()
        )
        flags = select(account.label("account_active"), scope.label("scope_readable")).cte("scope")
        header = (
            select(
                Canvas.id.label("canvas_id"),
                Canvas.board_id,
                Canvas.shelf_id,
                Canvas.author_id,
                CanvasPublication.title,
                CanvasPublication.summary,
                CanvasPublication.visibility,
                CanvasPublication.publication_revision,
                CanvasPublication.source_metadata_revision,
                CanvasPublication.source_document_revision,
                CanvasPublication.published_at,
                shelves.c.board_slug,
                shelves.c.board_name,
                shelves.c.shelf_slug,
                shelves.c.shelf_name,
            )
            .join(CanvasPublication, CanvasPublication.canvas_id == Canvas.id)
            .join(
                shelves,
                and_(shelves.c.board_id == Canvas.board_id, shelves.c.shelf_id == Canvas.shelf_id),
            )
            .where(
                Canvas.status == "draft",
                or_(
                    shelves.c.active_member,
                    and_(Canvas.visibility == "public", CanvasPublication.visibility == "public"),
                ),
            )
        )
        if query.board_id is not None:
            header = header.where(Canvas.board_id == query.board_id)
        if query.shelf_id is not None:
            header = header.where(Canvas.shelf_id == query.shelf_id)
        if query.interest_id is not None:
            header = header.where(
                exists().where(
                    BoardInterest.board_id == Canvas.board_id,
                    BoardInterest.interest_id == Interest.id,
                    Interest.slug == query.interest_id,
                    Interest.active.is_(True),
                )
            )
        if query.tag_id is not None:
            header = header.where(
                exists().where(
                    CanvasPublicationTag.canvas_id == Canvas.id,
                    CanvasPublicationTag.tag_id == query.tag_id,
                )
            )
        if before is not None:
            timestamp, canvas_id = before
            header = header.where(
                or_(
                    CanvasPublication.published_at < timestamp,
                    and_(CanvasPublication.published_at == timestamp, Canvas.id < canvas_id),
                )
            )
        page = (
            header.order_by(CanvasPublication.published_at.desc(), Canvas.id.desc())
            .limit(query.limit + 1)
            .cte("page")
        )
        statement = (
            select(
                flags,
                page,
                CanvasPublicationTag.tag_id,
                CanvasPublicationTag.name.label("tag_name"),
            )
            .select_from(flags)
            .outerjoin(page, and_(flags.c.account_active, flags.c.scope_readable))
            .outerjoin(CanvasPublicationTag, CanvasPublicationTag.canvas_id == page.c.canvas_id)
            .order_by(
                page.c.published_at.desc(), page.c.canvas_id.desc(), CanvasPublicationTag.position
            )
        )
        try:
            async with get_db() as db:
                # One SELECT: statement MVCC covers policy, header, relations and tags.
                rows = (await db.execute(statement)).mappings().all()
        except SQLAlchemyError as error:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE) from error
        items: dict[UUID, CanvasFeedItem] = {}
        for row in rows:
            if row["canvas_id"] is None:
                continue
            item = items.get(row["canvas_id"])
            if item is None:
                item = CanvasFeedItem(
                    publication_revision=row["publication_revision"],
                    source_metadata_revision=row["source_metadata_revision"],
                    source_document_revision=row["source_document_revision"],
                    published_at=as_utc(row["published_at"]).astimezone(UTC),
                    canvas=CanvasPublicationMetadata(
                        id=row["canvas_id"],
                        board_id=row["board_id"],
                        shelf_id=row["shelf_id"],
                        author_id=row["author_id"],
                        title=row["title"],
                        summary=row["summary"],
                        visibility=row["visibility"],
                        tags=[],
                    ),
                    board=CanvasFeedLocation(
                        id=row["board_id"], slug=row["board_slug"], name=row["board_name"]
                    ),
                    shelf=CanvasFeedLocation(
                        id=row["shelf_id"], slug=row["shelf_slug"], name=row["shelf_name"]
                    ),
                )
                items[row["canvas_id"]] = item
            if row["tag_id"] is not None:
                item.canvas.tags.append(TagResponse(id=row["tag_id"], name=row["tag_name"]))
        return CanvasFeedRows(
            bool(rows[0]["account_active"]), bool(rows[0]["scope_readable"]), list(items.values())
        )
