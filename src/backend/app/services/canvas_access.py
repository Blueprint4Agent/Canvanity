"""Shared current author/Board policy and lock ordering for Canvas resources."""

from datetime import datetime, timedelta
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
    CanvasPublication,
    CanvasTransaction,
    as_utc,
    utc_now,
)
from app.services.board_permission import BoardPermissionService


class CanvasAccessService:
    def __init__(self, permissions: BoardPermissionService = Depends()):
        self.permissions = permissions

    @staticmethod
    def trash_expires_at(canvas: Canvas) -> datetime | None:
        return (
            as_utc(canvas.trashed_at) + timedelta(days=CANVAS_TRASH_RETENTION_DAYS)
            if canvas.trashed_at is not None
            else None
        )

    @classmethod
    def trash_expired(cls, canvas: Canvas, *, at: datetime | None = None) -> bool:
        expires = cls.trash_expires_at(canvas)
        return expires is not None and (at if at is not None else utc_now()) >= expires

    @classmethod
    def capabilities(
        cls,
        board: Board,
        canvas: Canvas,
        *,
        can_write: bool,
        published: bool,
        at: datetime | None = None,
    ) -> CanvasCapabilities:
        """Author read is established before this pure projection; staff is not ownership."""
        draft = canvas.status == "draft"
        return CanvasCapabilities(
            read_document=True,
            edit_metadata=draft and can_write,
            edit_document=draft and can_write,
            trash=draft and board.status == "active",
            restore=canvas.status == "trashed"
            and can_write
            and not cls.trash_expired(canvas, at=at),
            publish=draft and can_write,
            unpublish=published and board.status == "active",
        )

    async def board(
        self,
        tx: CanvasTransaction,
        user_id: int | None,
        board_id: UUID,
        *,
        write: bool,
        read_lock: bool = False,
    ) -> tuple[Board, BoardMember | None]:
        board = (
            await tx.board.locked_board(board_id)
            if write
            else await tx.board.read_board(board_id, locked=read_lock)
        )
        if board is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        member = await tx.board.member(board.id, user_id) if user_id is not None else None
        try:
            self.permissions.check_read(board, member)
        except BoardException as error:
            if error.code.error == BoardErrorCode.NOT_FOUND.code.error:
                raise CanvasException(CanvasErrorCode.NOT_FOUND) from None
            raise
        return board, member

    @staticmethod
    async def active_account(tx: CanvasTransaction, user_id: int) -> None:
        # Lock before Canvas rows, matching account deletion's User -> Canvas FK update.
        if not await tx.board.lock_active_user(user_id):
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

    async def context(
        self, tx: CanvasTransaction, user_id: int, canvas_id: UUID, *, write: bool = False
    ) -> tuple[Board, BoardMember, Canvas]:
        board_id = await tx.board_id(canvas_id)
        if board_id is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        board, member = await self.board(tx, user_id, board_id, write=write)
        if write:
            await self.active_account(tx, user_id)
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

    async def read_context(
        self,
        tx: CanvasTransaction,
        user_id: int | None,
        canvas_id: UUID,
        *,
        view: str | None = None,
    ) -> tuple[Board, BoardMember | None, Canvas, CanvasPublication | None]:
        """Coherent current policy plus an explicit owner draft or published snapshot."""
        board_id = await tx.board_id(canvas_id)
        if board_id is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        board, member = await self.board(tx, user_id, board_id, write=False, read_lock=True)
        if user_id is not None:
            await self.active_account(tx, user_id)
        canvas = await tx.canvas(canvas_id, shared=True)
        if canvas is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        own = user_id is not None and canvas.author_id == user_id
        if view == "draft" or (view is None and own):
            if not own or member is None or member.status != "active":
                raise CanvasException(CanvasErrorCode.NOT_FOUND)
            return board, member, canvas, None
        publication = await tx.publication(canvas.id)
        if canvas.status != "draft" or publication is None:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        if "members" in (canvas.visibility, publication.visibility) and (
            member is None or member.status != "active"
        ):
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        grades = {grade.id: grade for grade in await tx.board.grades(board.id)}
        policies, overrides = await tx.board.policy_rows(board.id)
        if not self.permissions.shelf_capabilities(
            board, member, canvas.shelf_id, grades, policies, overrides
        )["read_canvas"]:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        return board, member, canvas, publication

    async def can_write(
        self, tx: CanvasTransaction, board: Board, member: BoardMember, shelf_id: UUID
    ) -> bool:
        grades = {grade.id: grade for grade in await tx.board.grades(board.id)}
        policies, overrides = await tx.board.policy_rows(board.id)
        return self.permissions.shelf_capabilities(
            board, member, shelf_id, grades, policies, overrides
        )["create_canvas"]

    async def require_write(
        self, tx: CanvasTransaction, board: Board, member: BoardMember, shelf_id: UUID
    ) -> None:
        if not await self.can_write(tx, board, member, shelf_id):
            raise CanvasException(CanvasErrorCode.FORBIDDEN)

    @staticmethod
    async def shelf(tx: CanvasTransaction, board_id: UUID, shelf_id: UUID) -> Shelf:
        shelf = await tx.shelf(board_id, shelf_id)
        if shelf is None or shelf.classification != "manual":
            raise CanvasException(CanvasErrorCode.INVALID_SHELF)
        return shelf
