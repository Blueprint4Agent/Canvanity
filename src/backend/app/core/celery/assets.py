"""Beat recovers due uploads, deletions and expired cleanup leases."""

import asyncio

from app.core.celery.app import celery_app
from app.core.observability.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="canvanity.assets.cleanup")
def cleanup_assets() -> None:
    from app.services.asset_cleanup import run_asset_cleanup

    result = asyncio.run(run_asset_cleanup())
    log = logger.warning if result["attention"] else logger.info
    log(
        "Asset cleanup batch completed (done=%s, failed=%s, attention=%s).",
        result["done"],
        result["failed"],
        len(result["attention"]),
    )
