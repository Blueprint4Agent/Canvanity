"""Private Canvas images with durable upload intent and cleanup, outside DB locks."""

import asyncio
import hashlib
from collections.abc import AsyncIterable
from dataclasses import dataclass
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import Depends
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.core.object_storage import ObjectStorage, StorageError, StorageErrorCode
from app.core.object_storage.identity import StorageLocation
from app.core.observability.logging import get_logger
from app.deps import get_object_storage, get_object_storage_location
from app.models.asset import Asset, AssetRepository, AssetResponse
from app.models.canvas import as_utc
from app.services.canvas_access import CanvasAccessService

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGE_FRAMES = 100
logger = get_logger(__name__)


@dataclass(frozen=True)
class NormalizedImage:
    data: bytes
    width: int
    height: int
    frames: int


def normalize_canvas_image(data: bytes) -> NormalizedImage:
    try:
        with Image.open(BytesIO(data), formats=["PNG", "JPEG", "WEBP", "GIF"]) as source:
            count = getattr(source, "n_frames", 1)
            if (
                not 1 <= count <= MAX_IMAGE_FRAMES
                or source.width * source.height * count > MAX_IMAGE_PIXELS
            ):
                raise ValueError("image bound")
            frames, durations = [], []
            for index in range(count):
                source.seek(index)
                source.load()
                frame = ImageOps.exif_transpose(source).convert("RGBA")
                frame.info.clear()
                frames.append(frame)
                durations.append(max(20, min(10_000, int(source.info.get("duration", 100)))))
            output = BytesIO()
            options = {"quality": 85, "exif": b"", "xmp": b"", "icc_profile": b""}
            if count > 1:
                options.update(
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=int(source.info.get("loop", 0)),
                )
            frames[0].save(output, "WEBP", **options)
            encoded = output.getvalue()
            if len(encoded) > MAX_IMAGE_BYTES:
                raise AssetException(AssetErrorCode.TOO_LARGE)
            # Encoders may merge identical animation frames; report the actual normalized file.
            with Image.open(BytesIO(encoded)) as normalized:
                return NormalizedImage(
                    encoded, normalized.width, normalized.height, getattr(normalized, "n_frames", 1)
                )
    except (
        TypeError,
        OverflowError,
        ValueError,
        OSError,
        SyntaxError,
        EOFError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise AssetException(AssetErrorCode.INVALID_IMAGE) from None


class AssetService:
    def __init__(
        self,
        access: CanvasAccessService = Depends(),
        repository: AssetRepository = Depends(),
        storage: ObjectStorage = Depends(get_object_storage),
        location: StorageLocation = Depends(get_object_storage_location),
    ):
        self.access, self.repository, self.storage, self.location = (
            access,
            repository,
            storage,
            location,
        )

    @staticmethod
    def summary(asset: Asset) -> AssetResponse:
        return AssetResponse(
            id=asset.id,
            canvas_id=asset.canvas_id,
            content_type=asset.content_type,
            byte_size=asset.byte_size,
            width=asset.width,
            height=asset.height,
            frame_count=asset.frame_count,
            state=asset.state,
            expires_at=as_utc(asset.expires_at) if asset.expires_at else None,
            created_at=as_utc(asset.created_at),
            url=f"/api/v1/canvases/{asset.canvas_id}/assets/{asset.id}",
        )

    async def _failed(self, asset_id: UUID) -> None:
        try:
            await self.repository.upload_failed(asset_id)
        except AssetException:
            # The put-before-cleanup reservation remains durable even if this acceleration fails.
            logger.warning("Asset upload cleanup remains scheduled (asset_id=%s).", asset_id)

    async def upload(
        self, user_id: int, canvas_id: UUID, chunks: AsyncIterable[bytes]
    ) -> AssetResponse:
        async with self.repository.transaction(write=False) as tx:
            board, member, canvas = await self.access.context(tx.context, user_id, canvas_id)
            await self.access.require_write(tx.context, board, member, canvas.shelf_id)
            if canvas.status != "draft":
                raise CanvasException(CanvasErrorCode.INVALID_STATE)
        data = bytearray()
        async for chunk in chunks:
            if len(data) + len(chunk) > MAX_IMAGE_BYTES:
                raise AssetException(AssetErrorCode.TOO_LARGE)
            data.extend(chunk)
        image = await run_in_threadpool(normalize_canvas_image, bytes(data))
        asset_id = uuid4()
        key = f"canvas-assets/{asset_id}/{uuid4().hex}.webp"
        async with self.repository.transaction() as tx:
            board, member, canvas = await self.access.context(
                tx.context, user_id, canvas_id, write=True
            )
            await self.access.require_write(tx.context, board, member, canvas.shelf_id)
            if canvas.status != "draft":
                raise CanvasException(CanvasErrorCode.INVALID_STATE)
            await tx.reserve(
                canvas,
                user_id,
                asset_id=asset_id,
                object_key=key,
                fingerprint=self.location.fingerprint,
                location=self.location.descriptor,
                byte_size=len(image.data),
                width=image.width,
                height=image.height,
                frame_count=image.frames,
                sha256=hashlib.sha256(image.data).hexdigest(),
            )
        try:
            await self.storage.put(key, image.data, "image/webp")
            async with self.repository.transaction() as tx:
                board, member, canvas = await self.access.context(
                    tx.context, user_id, canvas_id, write=True
                )
                await self.access.require_write(tx.context, board, member, canvas.shelf_id)
                if canvas.status != "draft":
                    raise CanvasException(CanvasErrorCode.INVALID_STATE)
                asset = await tx.asset(asset_id, locked=True)
                if asset is None:
                    raise AssetException(AssetErrorCode.CONFLICT)
                await tx.ready(asset)
                result = self.summary(asset)
        except StorageError as error:
            await asyncio.shield(self._failed(asset_id))
            raise AssetException(
                AssetErrorCode.TOO_LARGE
                if error.code == StorageErrorCode.TOO_LARGE
                else AssetErrorCode.UNAVAILABLE
            ) from None
        except BaseException:
            await asyncio.shield(self._failed(asset_id))
            raise
        return result

    async def read(self, user_id: int, canvas_id: UUID, asset_id: UUID) -> bytes:
        async with self.repository.transaction(write=False) as tx:
            _, _, canvas = await self.access.context(tx.context, user_id, canvas_id)
            asset = await tx.asset(asset_id)
            if asset is None or asset.canvas_id != canvas.id or asset.state != "ready":
                raise AssetException(AssetErrorCode.NOT_FOUND)
            key, fingerprint, size, digest = (
                asset.object_key,
                asset.storage_fingerprint,
                asset.byte_size,
                asset.sha256,
            )
        if fingerprint != self.location.fingerprint:
            raise AssetException(AssetErrorCode.UNAVAILABLE)
        try:
            info = await self.storage.stat(key)
            if info.size != size or info.content_type != "image/webp":
                raise AssetException(AssetErrorCode.UNAVAILABLE)
            stored = await self.storage.get(key)
        except StorageError as error:
            raise AssetException(
                AssetErrorCode.NOT_FOUND
                if error.code == StorageErrorCode.NOT_FOUND
                else AssetErrorCode.UNAVAILABLE
            ) from None
        if len(stored.data) != size or hashlib.sha256(stored.data).hexdigest() != digest:
            raise AssetException(AssetErrorCode.UNAVAILABLE)
        return stored.data

    async def delete(self, user_id: int, canvas_id: UUID, asset_id: UUID) -> None:
        async with self.repository.transaction() as tx:
            _, _, canvas = await self.access.context(tx.context, user_id, canvas_id, write=True)
            asset = await tx.asset(asset_id, locked=True)
            if asset is None or asset.canvas_id != canvas.id:
                raise AssetException(AssetErrorCode.NOT_FOUND)
            await tx.request_delete(asset)
