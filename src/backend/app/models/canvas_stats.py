"""Minimal daily view records and statement-consistent activity aggregates."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import Date, ForeignKey, Index, delete, func, select, tuple_
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base
from app.models.canvas import CanvasLike, CanvasRepository, CanvasTransaction
from app.models.canvas_comment import CanvasComment
from app.utils.canvas_limits import CANVAS_VIEW_WINDOW_DAYS


class CanvasView(Base):
    __tablename__ = "canvas_views"
    __table_args__ = (
        Index("ix_canvas_views_window", "canvas_id", "viewed_on"),
        Index("ix_canvas_views_expiry", "viewed_on"),
        Index("ix_canvas_views_user", "user_id"),
    )
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    viewed_on: Mapped[date] = mapped_column(Date, primary_key=True)


@dataclass(frozen=True)
class CanvasActivityCounts:
    likes: int
    comments: int
    views: int
    recent_likes: int
    recent_comments: int


class CanvasStatsResponse(BaseModel):
    like_count: int = Field(ge=0)
    comment_count: int = Field(ge=0, description="현재 visible 댓글 수")
    view_count: int = Field(ge=0, description="최근30개 UTC 날짜의 계정별 일 조회 수 합계")
    activity_score: int = Field(
        ge=0, description="같은 기간 신규 좋아요+현재 visible 신규 댓글+view_count, 각1점"
    )
    window_days: int = CANVAS_VIEW_WINDOW_DAYS
    window_started_on: date
    as_of: datetime


class CanvasViewResponse(BaseModel):
    recorded: bool
    stats: CanvasStatsResponse


class CanvasStatsTransaction(CanvasTransaction):
    async def record_view(self, canvas_id: UUID, user_id: int, viewed_on: date) -> bool:
        if await self._db.get(CanvasView, (canvas_id, user_id, viewed_on)) is not None:
            return False
        self._db.add(CanvasView(canvas_id=canvas_id, user_id=user_id, viewed_on=viewed_on))
        await self._db.flush()
        return True

    async def activity_counts(
        self, canvas_id: UUID, *, at: datetime, start: date
    ) -> CanvasActivityCounts:
        since = datetime.combine(start, time.min, tzinfo=UTC)
        likes = (
            select(func.count()).select_from(CanvasLike).where(CanvasLike.canvas_id == canvas_id)
        )
        comments = (
            select(func.count())
            .select_from(CanvasComment)
            .where(CanvasComment.canvas_id == canvas_id, CanvasComment.status == "visible")
        )
        views = (
            select(func.count())
            .select_from(CanvasView)
            .where(
                CanvasView.canvas_id == canvas_id, CanvasView.viewed_on.between(start, at.date())
            )
        )
        recent_likes = likes.where(CanvasLike.created_at.between(since, at))
        recent_comments = comments.where(CanvasComment.created_at.between(since, at))
        row = (
            await self._db.execute(
                select(
                    likes.scalar_subquery(),
                    comments.scalar_subquery(),
                    views.scalar_subquery(),
                    recent_likes.scalar_subquery(),
                    recent_comments.scalar_subquery(),
                )
            )
        ).one()
        return CanvasActivityCounts(*row)

    async def prune_views(self, before: date, *, limit: int) -> int:
        columns = (CanvasView.canvas_id, CanvasView.user_id, CanvasView.viewed_on)
        rows = (
            await self._db.execute(
                select(*columns)
                .where(CanvasView.viewed_on < before)
                .order_by(CanvasView.viewed_on, CanvasView.canvas_id, CanvasView.user_id)
                .limit(limit)
            )
        ).all()
        if not rows:
            return 0
        result = await self._db.execute(
            delete(CanvasView)
            .where(tuple_(*columns).in_([tuple(row) for row in rows]))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount


class CanvasStatsRepository(CanvasRepository):
    transaction_type = CanvasStatsTransaction
