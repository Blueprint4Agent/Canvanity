"""Community aggregate and transport schemas; no HTTP or provider dependencies."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base

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
