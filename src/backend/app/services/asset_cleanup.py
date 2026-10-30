"""Durable cleanup: claim/fence in DB, delete immutable objects outside transactions."""

import re
from uuid import UUID

from app.core.config.settings import SETTINGS
from app.core.db.session import dispose_db
from app.core.object_storage import ObjectStorage, StorageError, create_object_storage
from app.core.object_storage.identity import StorageLocation, object_storage_location
from app.models import api_key  # noqa: F401 - standalone workers must register User.api_keys.
from app.models.asset import AssetRepository


class AssetCleanupService:
    def __init__(
        self, repository: AssetRepository, storage: ObjectStorage, location: StorageLocation
    ):
        self.repository, self.storage, self.location = repository, storage, location

    async def drain(self, *, limit: int = 20) -> dict[str, int]:
        if not 1 <= limit <= 100:
            raise ValueError("Cleanup limit must be between 1 and 100.")
        counts = {"done": 0, "failed": 0, "skipped": 0}
        for job_id in await self.repository.due(limit=limit):
            claim = await self.repository.claim(job_id, self.location.fingerprint)
            if claim is None:
                counts["skipped"] += 1
                continue
            error = None
            if not re.fullmatch(
                rf"canvas-assets/{re.escape(str(claim.asset_id))}/[0-9a-f]{{32}}\.webp",
                claim.object_key,
            ):
                error = "invalid_key"
            else:
                try:
                    await self.storage.delete(claim.object_key)
                except StorageError as failure:
                    error = failure.code.value
            acknowledged = await self.repository.finish(claim, error=error)
            counts["skipped" if not acknowledged else "failed" if error else "done"] += 1
        return counts


async def run_asset_cleanup(*, limit: int = 20, retry_id: UUID | None = None) -> dict:
    location = object_storage_location(SETTINGS)
    storage = await create_object_storage(SETTINGS)
    try:
        repository = AssetRepository()
        if retry_id is not None:
            await repository.retry(retry_id)
        result = await AssetCleanupService(repository, storage, location).drain(limit=limit)
        result["attention"] = await repository.inventory(limit=limit)
        return result
    finally:
        try:
            await storage.close()
        finally:
            await dispose_db()
