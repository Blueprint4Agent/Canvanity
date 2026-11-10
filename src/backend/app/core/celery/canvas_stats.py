"""Remove expired daily-view records without retaining account identifiers in logs."""

import asyncio

from app.core.celery.app import celery_app
from app.core.db.session import dispose_db
from app.core.observability.logging import get_logger

logger = get_logger(__name__)


async def _cleanup() -> int:
    from app.models import api_key  # noqa: F401 - standalone workers register User.api_keys.
    from app.services.canvas_stats import cleanup_canvas_views

    try:
        return await cleanup_canvas_views()
    finally:
        await dispose_db()


@celery_app.task(name="canvanity.canvas_stats.cleanup")
def cleanup_canvas_view_records() -> None:
    count = asyncio.run(_cleanup())
    logger.info("Canvas view retention batch completed (deleted=%s).", count)
