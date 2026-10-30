"""Draft ownership and metadata workflows; operational roles never grant draft access."""

from datetime import timedelta
from uuid import UUID

from fastapi import Depends

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import Board, BoardMember, Shelf
from app.models.canvas import (
    CANVAS_TRASH_RETENTION_DAYS,
    Canvas,
    CanvasCapabilities,
    CanvasContent,
    CanvasCreateForm,
    CanvasDocumentResponse,
    CanvasMetadata,
    CanvasPatchForm,
    CanvasRepository,
    CanvasResponse,
    CanvasRevisionForm,
    CanvasTransaction,
    as_utc,
    utc_now,
)
from app.services.board_permission import BoardPermissionService


class CanvasService:
    def __init__(
        self,
        permissions: BoardPermissionService = Depends(),
        repository: CanvasRepository = Depends(),
    ):
        self.permissions = permissions
        self.repository = repository

    async def _board(
        self, tx: CanvasTransaction, user_id: int, board_id: UUID, *, write: bool
    ) -> tuple[Board, BoardMember | None]:
        board = (
            await tx.board.locked_board(board_id) if write else await tx.board.read_board(board_id)
        )
        if board is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        member = await tx.board.member(board.id, user_id)
        try:
            self.permissions.check_read(board, member)
        except BoardException as error:
            if error.code.error == BoardErrorCode.NOT_FOUND.code.error:
                raise CanvasException(CanvasErrorCode.NOT_FOUND) from None
            raise
        return board, member

    @staticmethod
    async def _active_account(tx: CanvasTransaction, user_id: int) -> None:
        # Lock before Canvas rows, matching account deletion's User -> Canvas FK update.
        if not await tx.board.lock_active_user(user_id):
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

    async def _context(
        self, tx: CanvasTransaction, user_id: int, canvas_id: UUID, *, write: bool = False
    ) -> tuple[Board, BoardMember, Canvas]:
        board_id = await tx.board_id(canvas_id)
        if board_id is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        board, member = await self._board(tx, user_id, board_id, write=write)
        if write:
            await self._active_account(tx, user_id)
        canvas = await tx.canvas(canvas_id, locked=write)
        if (
            canvas is None
            or canvas.author_id != user_id
            or member is None
            or member.status != "active"
        ):
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        if write and board.status != "active":
            raise CanvasException(CanvasErrorCode.FORBIDDEN)
        return board, member, canvas

    async def _can_write(
        self, tx: CanvasTransaction, board: Board, member: BoardMember, shelf_id: UUID
    ) -> bool:
        grades = {grade.id: grade for grade in await tx.board.grades(board.id)}
        policies, overrides = await tx.board.policy_rows(board.id)
        return self.permissions.shelf_capabilities(
            board, member, shelf_id, grades, policies, overrides
        )["create_canvas"]

    async def _require_write(
        self, tx: CanvasTransaction, board: Board, member: BoardMember, shelf_id: UUID
    ) -> None:
        if not await self._can_write(tx, board, member, shelf_id):
            raise CanvasException(CanvasErrorCode.FORBIDDEN)

    @staticmethod
    async def _shelf(tx: CanvasTransaction, board_id: UUID, shelf_id: UUID) -> Shelf:
        shelf = await tx.shelf(board_id, shelf_id)
        if shelf is None or shelf.classification != "manual":
            raise CanvasException(CanvasErrorCode.INVALID_SHELF)
        return shelf

    @staticmethod
    def _revision(canvas: Canvas, form: CanvasRevisionForm) -> None:
        if canvas.revision != form.expected_revision:
            raise CanvasException(CanvasErrorCode.CONFLICT, {"current_revision": canvas.revision})

    @staticmethod
    def _expired(canvas: Canvas) -> bool:
        return canvas.trashed_at is not None and as_utc(canvas.trashed_at) <= utc_now() - timedelta(
            days=CANVAS_TRASH_RETENTION_DAYS
        )

    async def _response(
        self, tx: CanvasTransaction, board: Board, member: BoardMember, canvas: Canvas
    ) -> CanvasResponse:
        document = await tx.document(canvas.id)
        if document is None:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE)
        can_write = await self._can_write(tx, board, member, canvas.shelf_id)
        return CanvasResponse(
            canvas=CanvasMetadata.model_validate(canvas),
            document_revision=document.revision,
            capabilities=CanvasCapabilities(
                read_document=True,
                edit_metadata=canvas.status == "draft" and can_write,
                trash=canvas.status == "draft" and board.status == "active",
                restore=canvas.status == "trashed" and can_write and not self._expired(canvas),
            ),
        )

    async def create(self, user_id: int, board_id: UUID, form: CanvasCreateForm) -> CanvasResponse:
        async with self.repository.transaction() as tx:
            board, member = await self._board(tx, user_id, board_id, write=True)
            if board.status != "active" or member is None or member.status != "active":
                raise CanvasException(CanvasErrorCode.FORBIDDEN)
            await self._active_account(tx, user_id)
            await self._shelf(tx, board.id, form.shelf_id)
            await self._require_write(tx, board, member, form.shelf_id)
            canvas = await tx.create(board.id, user_id, form)
            result = await self._response(tx, board, member, canvas)
        return result

    async def get(self, user_id: int, canvas_id: UUID) -> CanvasResponse:
        async with self.repository.transaction(write=False) as tx:
            board, member, canvas = await self._context(tx, user_id, canvas_id)
            return await self._response(tx, board, member, canvas)

    async def document(self, user_id: int, canvas_id: UUID) -> CanvasDocumentResponse:
        async with self.repository.transaction(write=False) as tx:
            _, _, canvas = await self._context(tx, user_id, canvas_id)
            document = await tx.document(canvas.id)
            if document is None:
                raise CanvasException(CanvasErrorCode.UNAVAILABLE)
            return CanvasDocumentResponse(
                document=CanvasContent.model_validate(document.document), revision=document.revision
            )

    async def change(self, user_id: int, canvas_id: UUID, form: CanvasPatchForm) -> CanvasResponse:
        async with self.repository.transaction() as tx:
            board, member, canvas = await self._context(tx, user_id, canvas_id, write=True)
            await self._require_write(tx, board, member, canvas.shelf_id)
            if form.shelf_id is not None and form.shelf_id != canvas.shelf_id:
                await self._shelf(tx, board.id, form.shelf_id)
                await self._require_write(tx, board, member, form.shelf_id)
            self._revision(canvas, form)
            if canvas.status != "draft":
                raise CanvasException(CanvasErrorCode.INVALID_STATE)
            await tx.patch(canvas, form)
            result = await self._response(tx, board, member, canvas)
        return result

    async def trash(self, user_id: int, canvas_id: UUID, form: CanvasRevisionForm) -> int:
        async with self.repository.transaction() as tx:
            _, _, canvas = await self._context(tx, user_id, canvas_id, write=True)
            self._revision(canvas, form)
            await tx.trash(canvas)
            revision = canvas.revision
        return revision

    async def restore(
        self, user_id: int, canvas_id: UUID, form: CanvasRevisionForm
    ) -> CanvasResponse:
        async with self.repository.transaction() as tx:
            board, member, canvas = await self._context(tx, user_id, canvas_id, write=True)
            await self._require_write(tx, board, member, canvas.shelf_id)
            self._revision(canvas, form)
            if self._expired(canvas):
                raise CanvasException(CanvasErrorCode.RESTORE_EXPIRED)
            await tx.restore(canvas)
            result = await self._response(tx, board, member, canvas)
        return result
