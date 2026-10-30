"""Shared current author/Board policy and lock ordering for Canvas resources."""

from uuid import UUID

from fastapi import Depends

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import Board, BoardMember, Shelf
from app.models.canvas import Canvas, CanvasTransaction
from app.services.board_permission import BoardPermissionService


class CanvasAccessService:
    def __init__(self, permissions: BoardPermissionService = Depends()):
        self.permissions = permissions

    async def board(
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
