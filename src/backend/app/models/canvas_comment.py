"""Comment records, bounded contracts and repository-owned persistence."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    and_,
    or_,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base
from app.models.canvas import CanvasRepository, CanvasTransaction, utc_now

CommentStatus = Literal["visible", "hidden", "deleted"]
CommentText = Annotated[
    str,
    BeforeValidator(lambda value: value.strip() if isinstance(value, str) else value),
    Field(min_length=1, max_length=5000),
]


class CanvasComment(Base):
    __tablename__ = "canvas_comments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('visible','hidden','deleted')", name="ck_canvas_comment_status"
        ),
        CheckConstraint("revision >= 0", name="ck_canvas_comment_revision"),
        CheckConstraint(
            "(status = 'deleted' AND body = '') OR (status <> 'deleted' AND length(body) BETWEEN 1 AND 5000)",
            name="ck_canvas_comment_body",
        ),
        Index("ix_canvas_comments_page", "canvas_id", "created_at", "id"),
        Index("ix_canvas_comments_author", "author_id"),
        Index("ix_canvas_comments_moderator", "moderated_by"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    canvas_id: Mapped[UUID] = mapped_column(ForeignKey("canvases.id", ondelete="CASCADE"))
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(String(5000))
    status: Mapped[str] = mapped_column(String(7), default="visible", server_default="visible")
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    moderated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    moderation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CommentCreateForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: CommentText


class CommentRevisionForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0, le=2**63 - 1, strict=True)


class CommentPatchForm(CommentRevisionForm):
    body: CommentText | None = None
    status: Literal["visible", "hidden"] | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=500)

    @model_validator(mode="after")
    def one_operation(self):
        if self.model_fields_set == {"expected_revision", "body"} and self.body is not None:
            return self
        if (
            self.model_fields_set == {"expected_revision", "status", "reason"}
            and self.status
            and self.reason
            and self.reason.strip()
        ):
            self.reason = self.reason.strip()
            return self
        raise ValueError("Change body, or moderate status with a reason.")


class CommentQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["visible", "all"] = "visible"
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, min_length=1, max_length=2048)


class CommentCapabilities(BaseModel):
    edit: bool
    delete: bool
    moderate: bool


class CommentResponse(BaseModel):
    id: UUID
    canvas_id: UUID
    author_id: int | None
    body: str | None
    status: CommentStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    capabilities: CommentCapabilities


class CommentPage(BaseModel):
    items: list[CommentResponse]
    next_cursor: str | None = None
    can_create: bool


class CommentTransaction(CanvasTransaction):
    async def comment(self, canvas_id: UUID, comment_id: UUID) -> CanvasComment | None:
        return await self._db.scalar(
            select(CanvasComment).where(
                CanvasComment.id == comment_id, CanvasComment.canvas_id == canvas_id
            )
        )

    async def comments(
        self, canvas_id: UUID, query: CommentQuery, before: tuple[datetime, UUID] | None
    ) -> list[CanvasComment]:
        statement = select(CanvasComment).where(CanvasComment.canvas_id == canvas_id)
        if query.status == "visible":
            statement = statement.where(CanvasComment.status == "visible")
        if before:
            at, comment_id = before
            statement = statement.where(
                or_(
                    CanvasComment.created_at < at,
                    and_(CanvasComment.created_at == at, CanvasComment.id < comment_id),
                )
            )
        return list(
            (
                await self._db.scalars(
                    statement.order_by(
                        CanvasComment.created_at.desc(), CanvasComment.id.desc()
                    ).limit(query.limit + 1)
                )
            ).all()
        )

    async def add_comment(self, canvas_id: UUID, user_id: int, body: str) -> CanvasComment:
        row = CanvasComment(canvas_id=canvas_id, author_id=user_id, body=body)
        self._db.add(row)
        await self._db.flush()
        return row

    async def change_comment(
        self,
        row: CanvasComment,
        *,
        body: str | None = None,
        status: str | None = None,
        actor_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        if body is not None:
            row.body = body
        if status is not None:
            row.status = status
            if status == "deleted":
                row.body = ""
            else:
                row.moderated_by, row.moderation_reason = actor_id, reason
        row.revision += 1
        row.updated_at = utc_now()
        await self._db.flush()


class CommentRepository(CanvasRepository):
    transaction_type = CommentTransaction
