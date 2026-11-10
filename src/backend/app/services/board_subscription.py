"""Subscriptions select feeds without conferring membership or permissions."""

from uuid import UUID

from fastapi import Depends

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import BoardRepository, BoardSubscriptionResponse
from app.services.board_permission import BoardPermissionService


class BoardSubscriptionService:
    def __init__(
        self,
        permissions: BoardPermissionService = Depends(),
        repository: BoardRepository = Depends(),
    ):
        self.permissions, self.repository = permissions, repository

    async def _context(self, tx, user_id, board_id, *, write):
        board = (
            await tx.locked_board(board_id) if write else await tx.read_board(board_id, locked=True)
        )
        if board is None:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        member = await tx.member(board_id, user_id)
        self.permissions.check_read(board, member)
        if not await tx.lock_active_user(user_id):
            raise AuthException(AuthErrorCode.USER_NOT_FOUND)
        return board

    async def get(self, user_id: int, board_id: UUID) -> BoardSubscriptionResponse:
        async with self.repository.transaction(write=False) as tx:
            await self._context(tx, user_id, board_id, write=False)
            return BoardSubscriptionResponse(subscribed=await tx.subscribed(board_id, user_id))

    async def set(
        self, user_id: int, board_id: UUID, *, subscribed: bool
    ) -> BoardSubscriptionResponse:
        async with self.repository.transaction() as tx:
            board = await self._context(tx, user_id, board_id, write=True)
            if subscribed and board.status != "active":
                raise BoardException(BoardErrorCode.FORBIDDEN)
            await tx.set_subscription(board_id, user_id, subscribed=subscribed)
            return BoardSubscriptionResponse(subscribed=subscribed)
