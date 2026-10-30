"""Community aggregate and transport schemas; no HTTP or provider dependencies."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    and_,
    delete,
    exists,
    func,
    or_,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.interest import Interest
from app.models.user import User

MAX_BOARD_USER_ID = 2**31 - 1
MAX_BOARD_GRADES = 20
MAX_GRADE_RANK = 2**31 - 1
GRADE_AUDIT_ACTIONS = frozenset(
    {"grade_created", "grade_updated", "grades_reordered", "grade_deleted"}
)

DocumentJSON = JSON().with_variant(JSONB(), "postgresql")
BoardVisibility = Literal["public", "private"]
BoardJoinPolicy = Literal["open", "invite"]
BoardAction = Literal["read_canvas", "create_canvas", "create_comment", "react"]
BoardMemberRole = Literal["owner", "admin", "moderator", "member"]
BoardMemberStatus = Literal["active", "pending", "suspended", "banned"]


def utc_now() -> datetime:
    return datetime.now(UTC)


class Board(Base):
    __tablename__ = "boards"
    __table_args__ = (
        CheckConstraint("visibility IN ('public','private')", name="ck_boards_visibility"),
        CheckConstraint("join_policy IN ('open','invite')", name="ck_boards_join_policy"),
        CheckConstraint(
            "visibility != 'private' OR join_policy = 'invite'", name="ck_boards_private_join"
        ),
        CheckConstraint("status IN ('active','suspended','archived')", name="ck_boards_status"),
        CheckConstraint("revision >= 0", name="ck_boards_revision"),
        Index("ix_boards_created_id", "created_at", "id"),
        Index("ix_boards_owner", "owner_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    rules: Mapped[str] = mapped_column(Text, default="", server_default="")
    visibility: Mapped[str] = mapped_column(String(10))
    join_policy: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(12), default="active", server_default="active")
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BoardMemberGrade(Base):
    __tablename__ = "board_member_grades"
    __table_args__ = (
        UniqueConstraint("board_id", "id", name="uq_board_grade_board_id"),
        UniqueConstraint("board_id", "name", name="uq_board_grade_name"),
        UniqueConstraint("board_id", "rank", name="uq_board_grade_rank"),
        CheckConstraint("rank >= 0", name="ck_board_grade_rank"),
        Index(
            "uq_board_grade_default",
            "board_id",
            unique=True,
            sqlite_where=text("is_default = 1"),
            postgresql_where=text("is_default"),
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(30))
    rank: Mapped[int] = mapped_column(Integer)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))


class BoardMember(Base):
    __tablename__ = "board_members"
    __table_args__ = (
        ForeignKeyConstraint(
            ["board_id", "grade_id"],
            ["board_member_grades.board_id", "board_member_grades.id"],
            name="fk_board_member_grade",
        ),
        CheckConstraint(
            "role IN ('owner','admin','moderator','member')", name="ck_board_member_role"
        ),
        CheckConstraint(
            "status IN ('active','pending','suspended','banned')", name="ck_board_member_status"
        ),
        Index("ix_board_members_page", "board_id", "joined_at", "user_id"),
        Index(
            "uq_board_member_owner",
            "board_id",
            unique=True,
            sqlite_where=text("role = 'owner'"),
            postgresql_where=text("role = 'owner'"),
        ),
    )
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    grade_id: Mapped[UUID] = mapped_column(Uuid)
    role: Mapped[str] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(12))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BoardInterest(Base):
    __tablename__ = "board_interests"
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    interest_id: Mapped[int] = mapped_column(
        ForeignKey("interests.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer)


class BoardPolicy(Base):
    __tablename__ = "board_policies"
    __table_args__ = (
        ForeignKeyConstraint(
            ["board_id", "min_grade_id"],
            ["board_member_grades.board_id", "board_member_grades.id"],
            name="fk_board_policy_grade",
        ),
        CheckConstraint(
            "action IN ('read_canvas','create_canvas','create_comment','react')",
            name="ck_board_policy_action",
        ),
        CheckConstraint("audience IN ('public','members')", name="ck_board_policy_audience"),
        CheckConstraint(
            "(audience = 'public' AND action = 'read_canvas' AND min_grade_id IS NULL AND NOT staff_only) OR (audience = 'members' AND ((staff_only AND min_grade_id IS NULL) OR (NOT staff_only AND min_grade_id IS NOT NULL)))",
            name="ck_board_policy_shape",
        ),
    )
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    action: Mapped[str] = mapped_column(String(20), primary_key=True)
    audience: Mapped[str] = mapped_column(String(10))
    min_grade_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    staff_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    staff_bypass: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Shelf(Base):
    __tablename__ = "shelves"
    __table_args__ = (
        UniqueConstraint("board_id", "id", name="uq_shelf_board_id"),
        UniqueConstraint("board_id", "slug", name="uq_shelf_slug"),
        CheckConstraint("purpose IN ('general','notice')", name="ck_shelf_purpose"),
        CheckConstraint("classification = 'manual'", name="ck_shelf_classification"),
        CheckConstraint("sort_order >= 0", name="ck_shelf_sort_order"),
        Index(
            "uq_shelf_default",
            "board_id",
            unique=True,
            sqlite_where=text("is_default = 1"),
            postgresql_where=text("is_default"),
        ),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(2000), default="", server_default="")
    icon: Mapped[str] = mapped_column(
        String(40), default="messages-square", server_default="messages-square"
    )
    sort_order: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(10))
    classification: Mapped[str] = mapped_column(
        String(10), default="manual", server_default="manual"
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ShelfPolicy(Base):
    __tablename__ = "shelf_policies"
    __table_args__ = (
        ForeignKeyConstraint(
            ["board_id", "shelf_id"],
            ["shelves.board_id", "shelves.id"],
            ondelete="CASCADE",
            name="fk_shelf_policy_shelf",
        ),
        ForeignKeyConstraint(
            ["board_id", "min_grade_id"],
            ["board_member_grades.board_id", "board_member_grades.id"],
            name="fk_shelf_policy_grade",
        ),
        CheckConstraint(
            "action IN ('read_canvas','create_canvas','create_comment','react')",
            name="ck_shelf_policy_action",
        ),
        CheckConstraint("audience IN ('public','members')", name="ck_shelf_policy_audience"),
        CheckConstraint(
            "(audience = 'public' AND action = 'read_canvas' AND min_grade_id IS NULL AND NOT staff_only) OR (audience = 'members' AND ((staff_only AND min_grade_id IS NULL) OR (NOT staff_only AND min_grade_id IS NOT NULL)))",
            name="ck_shelf_policy_shape",
        ),
    )
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    shelf_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    action: Mapped[str] = mapped_column(String(20), primary_key=True)
    audience: Mapped[str] = mapped_column(String(10))
    min_grade_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    staff_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    staff_bypass: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class BoardLayout(Base):
    __tablename__ = "board_layouts"
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), primary_key=True
    )
    document: Mapped[dict] = mapped_column(DocumentJSON)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class BoardMemberAudit(Base):
    __tablename__ = "board_member_audit"
    __table_args__ = (Index("ix_board_member_audit_page", "board_id", "created_at", "id"),)
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(40))
    changes: Mapped[dict] = mapped_column(DocumentJSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BoardCreateForm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(default="", max_length=2000)
    interest_ids: list[str] = Field(default_factory=list, max_length=3)
    visibility: BoardVisibility = "public"
    join_policy: BoardJoinPolicy = "open"

    @field_validator("slug")
    @classmethod
    def reserved_slug(cls, value: str) -> str:
        if value in {"new", "settings", "admin", "by-slug"}:
            raise ValueError("Reserved board address.")
        return value

    @field_validator("interest_ids")
    @classmethod
    def unique_interests(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value) or any(not item or len(item) > 40 for item in value):
            raise ValueError("Select up to three distinct official interests.")
        return value

    @model_validator(mode="after")
    def private_join(self):
        if self.visibility == "private" and self.join_policy != "invite":
            raise ValueError("Private boards require invite membership.")
        return self


class BoardDeleteForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    confirm_slug: str = Field(min_length=3, max_length=64)


class BoardSummary(BaseModel):
    id: UUID
    owner_id: int
    slug: str
    name: str
    description: str
    visibility: BoardVisibility
    join_policy: BoardJoinPolicy
    status: Literal["active", "archived", "suspended"]
    revision: int
    interest_ids: list[str]
    created_at: datetime


class BoardPageResponse(BaseModel):
    items: list[BoardSummary]
    next_cursor: str | None = None


class GradeSummary(BaseModel):
    id: UUID
    name: str
    rank: int
    is_default: bool


class MembershipSummary(BaseModel):
    role: BoardMemberRole
    status: BoardMemberStatus
    grade_id: UUID
    grade_name: str


class ShelfSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    icon: str
    purpose: Literal["general", "notice"]
    classification: Literal["manual"]
    sort_order: int
    is_default: bool
    capabilities: dict[BoardAction, bool]


class BoardHomeResponse(BaseModel):
    board: BoardSummary
    rules: str
    membership: MembershipSummary | None
    grades: list[GradeSummary]
    shelves: list[ShelfSummary]
    layout: dict
    layout_revision: int


def _patch_schema(schema: dict, changes: tuple[str, ...]) -> None:
    # Omission preserves a field; explicit null is invalid in the request contract.
    for field in changes:
        schema["properties"][field].pop("default", None)
    schema["allOf"] = [
        {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {field: schema["properties"][field]},
                    "required": [field],
                }
                for field in changes
            ]
        }
    ]


def _member_patch_schema(schema: dict) -> None:
    _patch_schema(schema, ("role", "status", "grade_id"))


def _grade_patch_schema(schema: dict) -> None:
    _patch_schema(schema, ("name", "is_default"))


class BoardGradeChangeForm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class BoardGradeCreateForm(BoardGradeChangeForm):
    name: str = Field(min_length=1, max_length=30)
    rank: int = Field(ge=0, le=MAX_GRADE_RANK, strict=True)


class BoardGradePatchForm(BoardGradeChangeForm):
    model_config = ConfigDict(json_schema_extra=_grade_patch_schema)
    name: Annotated[str, Field(min_length=1, max_length=30)] | SkipJsonSchema[None] = None
    is_default: Literal[True] | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def validate_changes(self):
        fields = self.model_fields_set & {"name", "is_default"}
        if not fields or any(getattr(self, field) is None for field in fields):
            raise ValueError("Provide a name or select this grade as the default.")
        return self


class BoardGradeOrderForm(BoardGradeChangeForm):
    grade_ids: list[UUID] = Field(min_length=1, max_length=MAX_BOARD_GRADES)

    @field_validator("grade_ids")
    @classmethod
    def unique_grades(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Grade IDs must be unique.")
        return value


class BoardGradeDeleteForm(BoardGradeChangeForm):
    replacement_grade_id: UUID


class BoardGradesResponse(BaseModel):
    items: list[GradeSummary]
    board_revision: int


class BoardGradeResponse(BaseModel):
    grade: GradeSummary
    board_revision: int


class BoardGradeAuditChange(BaseModel):
    before: list[GradeSummary]
    after: list[GradeSummary]
    replacement_grade_id: UUID | None = None
    reassigned_members: int = 0
    reassigned_board_policies: int = 0
    reassigned_shelf_policies: int = 0


class BoardMemberPatchForm(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, json_schema_extra=_member_patch_schema
    )
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)
    role: Literal["admin", "moderator", "member"] | SkipJsonSchema[None] = None
    status: Literal["active", "suspended", "banned"] | SkipJsonSchema[None] = None
    grade_id: UUID | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def validate_changes(self):
        fields = self.model_fields_set & {"role", "status", "grade_id"}
        if not fields or any(getattr(self, field) is None for field in fields):
            raise ValueError("Provide at least one non-null member change.")
        return self


class BoardMemberInviteForm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user_id: int = Field(gt=0, le=MAX_BOARD_USER_ID, strict=True)
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class BoardMembersQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=2048)
    q: str = Field(default="", max_length=200)
    role: BoardMemberRole | None = None
    status: BoardMemberStatus | None = None


class BoardAuditQuery(BaseModel):
    since: datetime
    until: datetime
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=2048)
    target_user_id: int | None = Field(default=None, gt=0, le=MAX_BOARD_USER_ID)


class BoardMemberPublic(BaseModel):
    user_id: int
    name: str
    handle: str | None


class BoardMemberDetail(BoardMemberPublic):
    role: BoardMemberRole
    status: BoardMemberStatus
    grade_id: UUID
    grade_name: str
    grade_rank: int
    joined_at: datetime


class BoardMemberListResponse(BaseModel):
    scope: Literal["management", "moderation"]
    items: list[BoardMemberDetail | BoardMemberPublic]
    next_cursor: str | None = None
    board_revision: int


class BoardMemberUpdateResponse(BaseModel):
    member: BoardMemberDetail
    board_revision: int


class BoardAuditState(BaseModel):
    role: BoardMemberRole | None = None
    status: BoardMemberStatus | None = None
    grade_id: UUID | None = None


class BoardMemberAuditResponse(BaseModel):
    id: UUID
    actor_user_id: int | None
    target_user_id: int | None
    action: str
    before: BoardAuditState | None = None
    after: BoardAuditState | None = None
    reason: str | None = None
    grade_change: BoardGradeAuditChange | None = None
    created_at: datetime


class BoardAuditPageResponse(BaseModel):
    items: list[BoardMemberAuditResponse]
    next_cursor: str | None = None
    board_revision: int


@dataclass
class BoardMemberData:
    member: BoardMember
    grade: BoardMemberGrade
    name: str
    handle: str | None


ACTIONS: tuple[BoardAction, ...] = ("read_canvas", "create_canvas", "create_comment", "react")


@dataclass
class BoardHomeData:
    board: Board
    member: BoardMember | None
    grades: list[BoardMemberGrade]
    policies: dict[str, BoardPolicy]
    overrides: dict[tuple[UUID, str], ShelfPolicy]
    shelves: list[Shelf]
    interests: list[str]
    layout: BoardLayout | None


@dataclass
class BoardGradeData:
    board: Board
    member: BoardMember | None
    grades: list[BoardMemberGrade]


class BoardTransaction:
    """Session remains private; callers use domain persistence operations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def lock_creator(self, user_id: int) -> bool:
        return (
            await self._db.scalar(
                select(User.id)
                .where(User.id == user_id, User.is_active.is_(True))
                .with_for_update()
            )
            is not None
        )

    async def owned_count(self, user_id: int) -> int:
        return await self._db.scalar(
            select(func.count()).select_from(Board).where(Board.owner_id == user_id)
        )

    async def slug_exists(self, slug: str) -> bool:
        return await self._db.scalar(select(Board.id).where(Board.slug == slug)) is not None

    async def active_interests(self, slugs: list[str]) -> dict[str, Interest]:
        rows = (
            await self._db.scalars(
                select(Interest).where(Interest.slug.in_(slugs), Interest.active.is_(True))
            )
        ).all()
        return {row.slug: row for row in rows}

    async def create_board(self, user_id: int, form: BoardCreateForm) -> Board:
        board = Board(
            owner_id=user_id,
            name=form.name,
            slug=form.slug,
            description=form.description,
            visibility=form.visibility,
            join_policy=form.join_policy,
        )
        self._db.add(board)
        await self._db.flush()
        return board

    async def locked_board(self, board_id: UUID) -> Board | None:
        return await self._db.scalar(select(Board).where(Board.id == board_id).with_for_update())

    async def member(self, board_id: UUID, user_id: int) -> BoardMember | None:
        return await self._db.get(BoardMember, (board_id, user_id))

    async def grade(self, grade_id: UUID) -> BoardMemberGrade | None:
        return await self._db.get(BoardMemberGrade, grade_id)

    async def default_grade(self, board_id: UUID) -> BoardMemberGrade | None:
        return await self._db.scalar(
            select(BoardMemberGrade).where(
                BoardMemberGrade.board_id == board_id, BoardMemberGrade.is_default.is_(True)
            )
        )

    async def grades(self, board_id: UUID) -> list[BoardMemberGrade]:
        return list(
            (
                await self._db.scalars(
                    select(BoardMemberGrade)
                    .where(BoardMemberGrade.board_id == board_id)
                    .order_by(BoardMemberGrade.rank, BoardMemberGrade.id)
                )
            ).all()
        )

    async def grade_listing(self, board_id: UUID, user_id: int | None) -> BoardGradeData | None:
        # One statement keeps the list, access context and revision in the same snapshot.
        rows = (
            await self._db.execute(
                select(Board, BoardMember, BoardMemberGrade)
                .outerjoin(
                    BoardMember,
                    and_(BoardMember.board_id == Board.id, BoardMember.user_id == user_id),
                )
                .outerjoin(BoardMemberGrade, BoardMemberGrade.board_id == Board.id)
                .where(Board.id == board_id)
                .order_by(BoardMemberGrade.rank, BoardMemberGrade.id)
            )
        ).all()
        if not rows:
            return None
        return BoardGradeData(
            rows[0][0], rows[0][1], [row[2] for row in rows if row[2] is not None]
        )

    @staticmethod
    def _grade_state(grades: list[BoardMemberGrade]) -> list[dict]:
        return [
            {"id": str(g.id), "name": g.name, "rank": g.rank, "is_default": g.is_default}
            for g in sorted(grades, key=lambda g: (g.rank, g.id))
        ]

    async def _record_grade_change(
        self,
        board: Board,
        actor_user_id: int,
        action: str,
        before: list[dict],
        grades: list[BoardMemberGrade],
        reason: str,
        **details,
    ) -> None:
        if not 1 <= len(grades) <= MAX_BOARD_GRADES or sum(g.is_default for g in grades) != 1:
            raise BoardException(BoardErrorCode.UNAVAILABLE)
        self._db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=actor_user_id,
                target_user_id=None,
                action=action,
                changes={
                    "before": before,
                    "after": self._grade_state(grades),
                    "reason": reason,
                    **details,
                },
            )
        )
        self._touch(board)
        await self._db.flush()

    async def create_grade(
        self,
        board: Board,
        actor_user_id: int,
        grades: list[BoardMemberGrade],
        form: BoardGradeCreateForm,
    ) -> BoardMemberGrade:
        before = self._grade_state(grades)
        grade = BoardMemberGrade(
            board_id=board.id, name=form.name, rank=form.rank, is_default=False
        )
        self._db.add(grade)
        await self._db.flush()
        grades.append(grade)
        await self._record_grade_change(
            board, actor_user_id, "grade_created", before, grades, form.reason
        )
        return grade

    async def change_grade(
        self,
        board: Board,
        actor_user_id: int,
        grades: list[BoardMemberGrade],
        grade: BoardMemberGrade,
        form: BoardGradePatchForm,
    ) -> BoardMemberGrade:
        before = self._grade_state(grades)
        if form.name is not None:
            grade.name = form.name
        if form.is_default and not grade.is_default:
            for current in grades:
                current.is_default = False
            # The partial unique index is immediate: clear before assigning the new default.
            await self._db.flush()
            grade.is_default = True
        if before != self._grade_state(grades):
            await self._record_grade_change(
                board, actor_user_id, "grade_updated", before, grades, form.reason
            )
        return grade

    async def reorder_grades(
        self,
        board: Board,
        actor_user_id: int,
        grades: list[BoardMemberGrade],
        form: BoardGradeOrderForm,
    ) -> list[BoardMemberGrade]:
        by_id = {grade.id: grade for grade in grades}
        ordered = [by_id[grade_id] for grade_id in form.grade_ids]
        if all(grade.rank == index * 10 for index, grade in enumerate(ordered)):
            return ordered
        before = self._grade_state(grades)
        # Avoid old and final ranks; adding to max(rank) could overflow PostgreSQL INTEGER.
        used = {g.rank for g in grades} | {index * 10 for index in range(len(grades))}
        candidate = 1
        for grade in ordered:
            while candidate in used:
                candidate += 1
            grade.rank = candidate
            used.add(candidate)
        await self._db.flush()
        for index, grade in enumerate(ordered):
            grade.rank = index * 10
        await self._db.flush()
        await self._record_grade_change(
            board, actor_user_id, "grades_reordered", before, ordered, form.reason
        )
        return ordered

    async def delete_grade(
        self,
        board: Board,
        actor_user_id: int,
        grades: list[BoardMemberGrade],
        grade: BoardMemberGrade,
        replacement: BoardMemberGrade,
        form: BoardGradeDeleteForm,
    ) -> list[BoardMemberGrade]:
        before = self._grade_state(grades)
        counts = {}
        for model, column, label in (
            (BoardMember, BoardMember.grade_id, "reassigned_members"),
            (BoardPolicy, BoardPolicy.min_grade_id, "reassigned_board_policies"),
            (ShelfPolicy, ShelfPolicy.min_grade_id, "reassigned_shelf_policies"),
        ):
            result = await self._db.execute(
                update(model)
                .where(model.board_id == board.id, column == grade.id)
                .values({column: replacement.id})
            )
            counts[label] = result.rowcount
        if grade.is_default:
            grade.is_default = False
            await self._db.flush()
            replacement.is_default = True
        await self._db.delete(grade)
        await self._db.flush()
        remaining = [g for g in grades if g.id != grade.id]
        await self._record_grade_change(
            board,
            actor_user_id,
            "grade_deleted",
            before,
            remaining,
            form.reason,
            replacement_grade_id=str(replacement.id),
            **counts,
        )
        return remaining

    async def member_count(self, board_id: UUID) -> int:
        return await self._db.scalar(
            select(func.count()).select_from(BoardMember).where(BoardMember.board_id == board_id)
        )

    async def invitable_user(self, user_id: int) -> bool:
        # A shared row lock keeps deactivation/deletion from changing this decision before commit.
        return (
            await self._db.scalar(
                select(User.id)
                .where(User.id == user_id, User.is_active.is_(True))
                .with_for_update(read=True)
            )
            is not None
        )

    def _new_member(self, board: Board, user_id: int, grade_id: UUID) -> BoardMember:
        member = BoardMember(
            board_id=board.id, user_id=user_id, grade_id=grade_id, role="member", status="active"
        )
        self._db.add(member)
        return member

    async def join_member(self, board: Board, user_id: int, grade_id: UUID) -> BoardMember:
        member = self._new_member(board, user_id, grade_id)
        self._db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=user_id,
                target_user_id=user_id,
                action="member_joined",
                changes={"role": "member", "status": "active", "grade_id": str(grade_id)},
            )
        )
        self._touch(board)
        return member

    async def invite_member(
        self, board: Board, actor_user_id: int, user_id: int, grade_id: UUID, reason: str
    ) -> BoardMemberData:
        member = self._new_member(board, user_id, grade_id)
        self._db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=actor_user_id,
                target_user_id=user_id,
                action="member_invited",
                changes={"before": None, "after": self._member_state(member), "reason": reason},
            )
        )
        self._touch(board)
        await self._db.flush()
        result = await self.member_details(board.id, user_id)
        if result is None:
            raise BoardException(BoardErrorCode.UNAVAILABLE)
        return result

    async def leave_member(self, board: Board, member: BoardMember) -> None:
        self._db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=member.user_id,
                target_user_id=member.user_id,
                action="member_left",
                changes={
                    "previous_role": member.role,
                    "previous_status": member.status,
                    "previous_grade_id": str(member.grade_id),
                },
            )
        )
        await self._db.delete(member)
        self._touch(board)

    @staticmethod
    def _touch(board: Board) -> None:
        board.revision += 1
        board.updated_at = utc_now()

    async def delete_board(self, board: Board) -> None:
        for model in (
            ShelfPolicy,
            BoardPolicy,
            BoardMemberAudit,
            BoardInterest,
            BoardLayout,
            BoardMember,
            Shelf,
            BoardMemberGrade,
        ):
            await self._db.execute(delete(model).where(model.board_id == board.id))
        await self._db.delete(board)

    async def read_board(self, board_id: UUID) -> Board | None:
        return await self._db.get(Board, board_id)

    @staticmethod
    def _member_statement(board_id: UUID):
        return (
            select(BoardMember, BoardMemberGrade, User.name, User.handle)
            .join(
                BoardMemberGrade,
                and_(
                    BoardMemberGrade.id == BoardMember.grade_id,
                    BoardMemberGrade.board_id == BoardMember.board_id,
                ),
            )
            .join(User, User.id == BoardMember.user_id)
            .where(BoardMember.board_id == board_id)
        )

    async def member_details(self, board_id: UUID, user_id: int) -> BoardMemberData | None:
        row = (
            await self._db.execute(
                self._member_statement(board_id).where(BoardMember.user_id == user_id)
            )
        ).one_or_none()
        return BoardMemberData(*row) if row is not None else None

    async def list_members(
        self,
        board_id: UUID,
        query: BoardMembersQuery,
        *,
        moderation_only: bool,
        before: tuple[datetime, int] | None,
    ) -> list[BoardMemberData]:
        statement = self._member_statement(board_id)
        if moderation_only:
            statement = statement.where(
                BoardMember.role == "member", BoardMember.status == "active"
            )
        if query.role is not None:
            statement = statement.where(BoardMember.role == query.role)
        if query.status is not None:
            statement = statement.where(BoardMember.status == query.status)
        if query.q.strip():
            statement = statement.where(
                or_(
                    User.name.icontains(query.q.strip(), autoescape=True),
                    User.handle.icontains(query.q.strip(), autoescape=True),
                )
            )
        if before:
            timestamp, user_id = before
            statement = statement.where(
                or_(
                    BoardMember.joined_at < timestamp,
                    and_(BoardMember.joined_at == timestamp, BoardMember.user_id < user_id),
                )
            )
        statement = statement.order_by(
            BoardMember.joined_at.desc(), BoardMember.user_id.desc()
        ).limit(query.limit + 1)
        return [BoardMemberData(*row) for row in (await self._db.execute(statement)).all()]

    @staticmethod
    def _member_state(member: BoardMember) -> dict:
        return {"role": member.role, "status": member.status, "grade_id": str(member.grade_id)}

    async def update_member(
        self, board: Board, member: BoardMember, actor_user_id: int, form: BoardMemberPatchForm
    ) -> BoardMemberData:
        previous = self._member_state(member)
        for field in ("role", "status", "grade_id"):
            if field in form.model_fields_set:
                setattr(member, field, getattr(form, field))
        current = self._member_state(member)
        if previous != current:
            self._db.add(
                BoardMemberAudit(
                    board_id=board.id,
                    actor_user_id=actor_user_id,
                    target_user_id=member.user_id,
                    action="member_updated",
                    changes={"before": previous, "after": current, "reason": form.reason},
                )
            )
            self._touch(board)
            await self._db.flush()
        result = await self.member_details(board.id, member.user_id)
        if result is None:
            raise BoardException(BoardErrorCode.MEMBER_NOT_FOUND)
        return result

    async def list_member_audit(
        self, board_id: UUID, query: BoardAuditQuery, *, before: tuple[datetime, UUID] | None
    ) -> list[BoardMemberAudit]:
        statement = select(BoardMemberAudit).where(
            BoardMemberAudit.board_id == board_id,
            BoardMemberAudit.created_at >= query.since,
            BoardMemberAudit.created_at <= query.until,
        )
        if query.target_user_id is not None:
            statement = statement.where(BoardMemberAudit.target_user_id == query.target_user_id)
        if before:
            timestamp, audit_id = before
            statement = statement.where(
                or_(
                    BoardMemberAudit.created_at < timestamp,
                    and_(BoardMemberAudit.created_at == timestamp, BoardMemberAudit.id < audit_id),
                )
            )
        return list(
            (
                await self._db.scalars(
                    statement.order_by(
                        BoardMemberAudit.created_at.desc(), BoardMemberAudit.id.desc()
                    ).limit(query.limit + 1)
                )
            ).all()
        )

    async def initialize(self, board: Board, user_id: int, interest_ids: list[int]) -> None:
        db = self._db
        grades = [
            BoardMemberGrade(board_id=board.id, name=name, rank=rank, is_default=rank == 0)
            for name, rank in (("뉴커머", 0), ("피너", 10), ("큐레이터", 20))
        ]
        db.add_all(grades)
        await db.flush()
        db.add(
            BoardMember(
                board_id=board.id,
                user_id=user_id,
                role="owner",
                status="active",
                grade_id=grades[0].id,
            )
        )
        for action in ACTIONS:
            public_read = action == "read_canvas" and board.visibility == "public"
            db.add(
                BoardPolicy(
                    board_id=board.id,
                    action=action,
                    audience="public" if public_read else "members",
                    min_grade_id=None
                    if public_read
                    else grades[1 if action == "create_canvas" else 0].id,
                    staff_only=False,
                    staff_bypass=True,
                )
            )
        db.add_all(
            [
                BoardInterest(board_id=board.id, interest_id=interest, position=index)
                for index, interest in enumerate(interest_ids)
            ]
        )
        shelves = [
            Shelf(
                board_id=board.id,
                name="공지사항",
                slug="notice",
                purpose="notice",
                sort_order=0,
                icon="megaphone",
                is_default=False,
            ),
            Shelf(
                board_id=board.id,
                name="자유 이야기",
                slug="general",
                purpose="general",
                sort_order=1,
                is_default=True,
            ),
        ]
        db.add_all(shelves)
        await db.flush()
        for action in ("create_canvas", "create_comment"):
            db.add(
                ShelfPolicy(
                    board_id=board.id,
                    shelf_id=shelves[0].id,
                    action=action,
                    audience="members",
                    min_grade_id=None,
                    staff_only=True,
                    staff_bypass=False,
                )
            )
        db.add(
            BoardLayout(
                board_id=board.id,
                document={
                    "schema_version": 1,
                    "widgets": [
                        {
                            "id": "board-intro",
                            "type": "board_intro",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 600, "height": 240},
                        },
                        {
                            "id": "shelves",
                            "type": "shelf_navigation",
                            "position": {"x": 100, "y": 420},
                            "size": {"width": 600, "height": 300},
                        },
                        {
                            "id": "latest",
                            "type": "canvas_collection",
                            "source": {"board_id": str(board.id), "sort": "latest", "limit": 6},
                            "position": {"x": 850, "y": 100},
                            "size": {"width": 850, "height": 650},
                        },
                    ],
                },
            )
        )
        db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=user_id,
                target_user_id=user_id,
                action="board_created",
                changes={"role": "owner", "grade_id": str(grades[0].id)},
            )
        )
        await db.flush()


class BoardRepository:
    @asynccontextmanager
    async def transaction(
        self, *, write: bool = True, create_slug: str | None = None, deleting: bool = False
    ) -> AsyncIterator[BoardTransaction]:
        try:
            async with get_db() as db:
                if write and db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                yield BoardTransaction(db)
                if write:
                    await db.commit()
        except IntegrityError as error:
            if deleting:
                raise BoardException(BoardErrorCode.NOT_EMPTY) from error
            if create_slug is not None:
                async with self.transaction(write=False) as tx:
                    if await tx.slug_exists(create_slug):
                        raise BoardException(BoardErrorCode.SLUG_TAKEN) from error
            raise BoardException(BoardErrorCode.UNAVAILABLE) from error
        except SQLAlchemyError as error:
            raise BoardException(BoardErrorCode.UNAVAILABLE) from error

    async def list_visible(
        self,
        user_id: int | None,
        *,
        limit: int,
        q: str,
        interest_id: str | None,
        mine: bool,
        before: tuple[datetime, UUID] | None,
    ) -> tuple[list[Board], dict[UUID, list[str]]]:
        clause = Board.visibility == "public"
        if user_id is not None:
            active_member = exists().where(
                BoardMember.board_id == Board.id,
                BoardMember.user_id == user_id,
                BoardMember.status == "active",
            )
            blocked_member = exists().where(
                BoardMember.board_id == Board.id,
                BoardMember.user_id == user_id,
                BoardMember.status.in_(["banned", "suspended"]),
            )
            clause = and_(or_(clause, active_member), ~blocked_member)
        query = select(Board).where(Board.status.in_(["active", "archived"]), clause)
        if mine:
            query = query.where(Board.owner_id == user_id)
        if q:
            query = query.where(Board.name.contains(q, autoescape=True))
        if interest_id:
            query = query.where(
                exists().where(
                    BoardInterest.board_id == Board.id,
                    BoardInterest.interest_id == Interest.id,
                    Interest.slug == interest_id,
                    Interest.active.is_(True),
                )
            )
        if before is not None:
            created, last_id = before
            query = query.where(
                or_(
                    Board.created_at < created,
                    and_(Board.created_at == created, Board.id < last_id),
                )
            )
        async with self.transaction(write=False) as tx:
            db = tx._db
            boards = list(
                (
                    await db.scalars(
                        query.order_by(Board.created_at.desc(), Board.id.desc()).limit(limit + 1)
                    )
                ).all()
            )
            selected = boards[:limit]
            interests = {board.id: [] for board in selected}
            for board_id, slug in (
                await db.execute(
                    select(BoardInterest.board_id, Interest.slug)
                    .join(Interest, Interest.id == BoardInterest.interest_id)
                    .where(BoardInterest.board_id.in_(interests), Interest.active.is_(True))
                    .order_by(BoardInterest.position)
                )
            ).all():
                interests[board_id].append(slug)
            return boards, interests

    async def home_data(
        self, user_id: int | None, *, board_id: UUID | None = None, slug: str | None = None
    ) -> BoardHomeData | None:
        async with self.transaction(write=False) as tx:
            db = tx._db
            board = await db.scalar(
                select(Board).where(
                    Board.id == board_id if board_id is not None else Board.slug == slug
                )
            )
            if board is None:
                return None
            member = await tx.member(board.id, user_id) if user_id is not None else None
            grades = list(
                (
                    await db.scalars(
                        select(BoardMemberGrade)
                        .where(BoardMemberGrade.board_id == board.id)
                        .order_by(BoardMemberGrade.rank)
                    )
                ).all()
            )
            policies = {
                p.action: p
                for p in (
                    await db.scalars(select(BoardPolicy).where(BoardPolicy.board_id == board.id))
                ).all()
            }
            overrides = {
                (p.shelf_id, p.action): p
                for p in (
                    await db.scalars(select(ShelfPolicy).where(ShelfPolicy.board_id == board.id))
                ).all()
            }
            shelves = list(
                (
                    await db.scalars(
                        select(Shelf)
                        .where(Shelf.board_id == board.id, Shelf.is_visible.is_(True))
                        .order_by(Shelf.sort_order, Shelf.id)
                    )
                ).all()
            )
            interests = list(
                (
                    await db.scalars(
                        select(Interest.slug)
                        .join(BoardInterest, BoardInterest.interest_id == Interest.id)
                        .where(BoardInterest.board_id == board.id, Interest.active.is_(True))
                        .order_by(BoardInterest.position)
                    )
                ).all()
            )
            layout = await db.get(BoardLayout, board.id)
            return BoardHomeData(
                board, member, grades, policies, overrides, shelves, interests, layout
            )
