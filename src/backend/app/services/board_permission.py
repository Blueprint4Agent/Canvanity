"""Board role, grade and status evaluation without database access."""

from uuid import UUID

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import Board, BoardMember, BoardMemberGrade, BoardPolicy, ShelfPolicy

STAFF = {"owner", "admin", "moderator"}


class BoardPermissionService:
    @staticmethod
    def check_read(board: Board, member: BoardMember | None) -> None:
        if member and member.status in {"suspended", "banned"}:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        if board.visibility == "private" and (member is None or member.status != "active"):
            raise BoardException(BoardErrorCode.NOT_FOUND)

    @staticmethod
    def allowed(
        board: Board,
        member: BoardMember | None,
        policy: BoardPolicy | ShelfPolicy | None,
        grades: dict[UUID, BoardMemberGrade],
        action: str,
    ) -> bool:
        if policy is None or (action != "read_canvas" and board.status != "active"):
            return False
        if policy.audience == "public" and action == "read_canvas" and board.visibility == "public":
            return True
        if member is None or member.status != "active":
            return False
        staff = member.role in STAFF
        if policy.staff_only:
            return staff
        if staff and policy.staff_bypass:
            return True
        own = grades.get(member.grade_id)
        minimum = grades.get(policy.min_grade_id)
        return own is not None and minimum is not None and own.rank >= minimum.rank
