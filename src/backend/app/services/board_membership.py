"""Membership policies use the model Repository's locked aggregate transaction."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import BoardRepository, MembershipSummary
from app.services.board_permission import BoardPermissionService


class BoardMembershipService:
    def __init__(
        self,
        permissions: Annotated[BoardPermissionService, Depends()],
        repository: Annotated[BoardRepository, Depends()],
    ):
        self.permissions = permissions
        self.repository = repository

    async def join(self, user_id: int, board_id: UUID) -> MembershipSummary:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None or board.status == "suspended":
                raise BoardException(BoardErrorCode.NOT_FOUND)
            member = await tx.member(board_id, user_id)
            if member and member.status != "active":
                raise BoardException(BoardErrorCode.FORBIDDEN)
            if member or board.visibility == "public":
                self.permissions.check_read(board, member)
            if member:
                grade = await tx.grade(member.grade_id)
            else:
                if (
                    board.status != "active"
                    or board.visibility != "public"
                    or board.join_policy != "open"
                ):
                    raise BoardException(BoardErrorCode.FORBIDDEN)
                grade = await tx.default_grade(board_id)
                if grade is None:
                    raise BoardException(BoardErrorCode.UNAVAILABLE)
                member = await tx.join_member(board, user_id, grade.id)
            if grade is None or grade.board_id != board_id:
                raise BoardException(BoardErrorCode.UNAVAILABLE)
            result = MembershipSummary(
                role=member.role, status=member.status, grade_id=grade.id, grade_name=grade.name
            )
        return result

    async def leave(self, user_id: int, board_id: UUID) -> None:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            member = await tx.member(board_id, user_id)
            self.permissions.check_read(board, member)
            if member is None:
                return
            if member.status != "active":
                raise BoardException(BoardErrorCode.FORBIDDEN)
            if board.owner_id == user_id or member.role == "owner":
                raise BoardException(BoardErrorCode.OWNER_CANNOT_LEAVE)
            await tx.leave_member(board, member)
