"""Current Board policy and private image I/O, outside persistence transactions."""

import asyncio
import hashlib
from collections.abc import AsyncIterable
from uuid import UUID, uuid4

from fastapi import Depends
from starlette.concurrency import run_in_threadpool

from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.core.object_storage import ObjectStorage, StorageError, StorageErrorCode
from app.core.object_storage.identity import StorageLocation
from app.core.observability.logging import get_logger
from app.deps import get_object_storage, get_object_storage_location
from app.models.board_media import (
    MAX_BOARD_REVISION,
    BoardMediaChangeForm,
    BoardMediaRepository,
    BoardMediaSlot,
    BoardMediaTransaction,
    BoardMediaUpdateResponse,
)
from app.services.asset import MAX_IMAGE_BYTES, normalize_canvas_image
from app.services.board_permission import BoardPermissionService
from app.utils.asset_keys import valid_asset_key

logger = get_logger(__name__)


class BoardMediaService:
    def __init__(
        self,
        permissions: BoardPermissionService = Depends(),
        repository: BoardMediaRepository = Depends(),
        storage: ObjectStorage = Depends(get_object_storage),
        location: StorageLocation = Depends(get_object_storage_location),
    ):
        self.permissions, self.repository, self.storage, self.location = (
            permissions,
            repository,
            storage,
            location,
        )

    async def _write_context(
        self, tx: BoardMediaTransaction, user_id: int, board_id: UUID, expected_revision: int
    ):
        board = await tx.board.locked_board(board_id)
        if board is None:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        if not await tx.board.lock_active_user(user_id):
            raise BoardException(BoardErrorCode.NOT_FOUND)
        member = await tx.board.member(board.id, user_id)
        self.permissions.check_manage_structure(board, member, write=True)
        if board.revision != expected_revision:
            raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
        return board

    async def _failed(self, asset_id: UUID) -> None:
        try:
            await self.repository.upload_failed(asset_id)
        except (AssetException, BoardException):
            logger.warning("Board media cleanup remains scheduled (asset_id=%s).", asset_id)

    async def upload(
        self,
        user_id: int,
        board_id: UUID,
        slot: BoardMediaSlot,
        form: BoardMediaChangeForm,
        chunks: AsyncIterable[bytes],
    ) -> BoardMediaUpdateResponse:
        # Permission and CAS precede reading/decoding the bounded multipart file.
        async with self.repository.transaction() as tx:
            board = await self._write_context(tx, user_id, board_id, form.expected_revision)
            if board.revision >= MAX_BOARD_REVISION:
                raise BoardException(BoardErrorCode.REVISION_EXHAUSTED)
        data = bytearray()
        async for chunk in chunks:
            if len(data) + len(chunk) > MAX_IMAGE_BYTES:
                raise AssetException(AssetErrorCode.TOO_LARGE)
            data.extend(chunk)
        image = await run_in_threadpool(normalize_canvas_image, bytes(data))
        asset_id = uuid4()
        key = f"board-media/{asset_id}/{uuid4().hex}.webp"
        async with self.repository.transaction() as tx:
            board = await self._write_context(tx, user_id, board_id, form.expected_revision)
            await tx.reserve(
                board,
                user_id,
                id=asset_id,
                slot=slot,
                object_key=key,
                storage_fingerprint=self.location.fingerprint,
                storage_location=self.location.descriptor,
                byte_size=len(image.data),
                width=image.width,
                height=image.height,
                frame_count=image.frames,
                sha256=hashlib.sha256(image.data).hexdigest(),
            )
        try:
            await self.storage.put(key, image.data, "image/webp")
            async with self.repository.transaction() as tx:
                board = await self._write_context(tx, user_id, board_id, form.expected_revision)
                result = await tx.select(board, user_id, slot, asset_id, form.reason)
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

    async def remove(
        self, user_id: int, board_id: UUID, slot: BoardMediaSlot, form: BoardMediaChangeForm
    ) -> BoardMediaUpdateResponse:
        async with self.repository.transaction() as tx:
            board = await self._write_context(tx, user_id, board_id, form.expected_revision)
            result = await tx.select(board, user_id, slot, None, form.reason)
        return result

    async def _read_context(
        self, user_id: int | None, board_id: UUID, slot: BoardMediaSlot, asset_id: UUID
    ) -> tuple:
        async with self.repository.transaction(write=False) as tx:
            board = await tx.board.read_board(board_id)
            if board is None or (user_id is not None and not await tx.account_active(user_id)):
                raise BoardException(BoardErrorCode.MEDIA_NOT_FOUND)
            member = await tx.board.member(board_id, user_id) if user_id is not None else None
            self.permissions.check_read(board, member)
            asset = await tx.current(board_id, slot, asset_id)
            if asset is None:
                raise BoardException(BoardErrorCode.MEDIA_NOT_FOUND)
            return (
                asset.object_key,
                asset.storage_fingerprint,
                asset.storage_location,
                asset.byte_size,
                asset.sha256,
            )

    async def read(
        self, user_id: int | None, board_id: UUID, slot: BoardMediaSlot, asset_id: UUID
    ) -> bytes:
        context = await self._read_context(user_id, board_id, slot, asset_id)
        key, fingerprint, location, size, digest = context
        if (
            fingerprint != self.location.fingerprint
            or location != self.location.descriptor
            or not valid_asset_key(key, asset_id, namespace="board-media")
        ):
            raise AssetException(AssetErrorCode.UNAVAILABLE)
        try:
            info = await self.storage.stat(key)
            if info.size != size or info.content_type != "image/webp":
                raise AssetException(AssetErrorCode.UNAVAILABLE)
            stored = await self.storage.get(key)
        except StorageError as error:
            if error.code == StorageErrorCode.NOT_FOUND:
                raise BoardException(BoardErrorCode.MEDIA_NOT_FOUND) from None
            raise AssetException(AssetErrorCode.UNAVAILABLE) from None
        if (
            stored.metadata.key != key
            or stored.metadata.content_type != "image/webp"
            or stored.metadata.size != size
            or len(stored.data) != size
            or hashlib.sha256(stored.data).hexdigest() != digest
        ):
            raise AssetException(AssetErrorCode.UNAVAILABLE)
        if await self._read_context(user_id, board_id, slot, asset_id) != context:
            raise BoardException(BoardErrorCode.MEDIA_NOT_FOUND)
        return stored.data
