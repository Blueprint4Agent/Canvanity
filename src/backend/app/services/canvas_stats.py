"""Current access, UTC windows and explicit daily-view/activity policy."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends

from app.models.canvas import utc_now
from app.models.canvas_stats import CanvasStatsRepository, CanvasStatsResponse, CanvasViewResponse
from app.services.canvas_access import CanvasAccessService
from app.utils.canvas_limits import CANVAS_VIEW_CLEANUP_BATCH_SIZE, CANVAS_VIEW_WINDOW_DAYS


def view_window_start(at: datetime):
    return at.astimezone(UTC).date() - timedelta(days=CANVAS_VIEW_WINDOW_DAYS - 1)


class CanvasStatsService:
    def __init__(
        self, access: CanvasAccessService = Depends(), repository: CanvasStatsRepository = Depends()
    ):
        self.access, self.repository = access, repository

    @staticmethod
    async def _statistics(tx, canvas_id, at):
        start = view_window_start(at)
        counts = await tx.activity_counts(canvas_id, at=at, start=start)
        return CanvasStatsResponse(
            like_count=counts.likes,
            comment_count=counts.comments,
            view_count=counts.views,
            activity_score=counts.recent_likes + counts.recent_comments + counts.views,
            window_started_on=start,
            as_of=at,
        )

    async def get(self, user_id: int | None, canvas_id: UUID) -> CanvasStatsResponse:
        async with self.repository.transaction(write=False) as tx:
            await self.access.read_context(
                tx, user_id, canvas_id, view="publication", metadata_only=True
            )
            return await self._statistics(tx, canvas_id, utc_now())

    async def record(self, user_id: int, canvas_id: UUID) -> CanvasViewResponse:
        async with self.repository.transaction() as tx:
            await self.access.read_context(
                tx, user_id, canvas_id, view="publication", write=True, metadata_only=True
            )
            at = utc_now()
            recorded = await tx.record_view(canvas_id, user_id, at.date())
            return CanvasViewResponse(
                recorded=recorded, stats=await self._statistics(tx, canvas_id, at)
            )


async def cleanup_canvas_views(
    *,
    repository: CanvasStatsRepository | None = None,
    at: datetime | None = None,
    limit: int = CANVAS_VIEW_CLEANUP_BATCH_SIZE,
) -> int:
    if type(limit) is not int or not 1 <= limit <= CANVAS_VIEW_CLEANUP_BATCH_SIZE:
        raise ValueError("Invalid view cleanup batch size.")
    repository = repository if repository is not None else CanvasStatsRepository()
    async with repository.transaction() as tx:
        return await tx.prune_views(
            view_window_start(at if at is not None else utc_now()), limit=limit
        )
