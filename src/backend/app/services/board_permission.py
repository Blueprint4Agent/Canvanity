"""Current Board context policy evaluation, independent from app-wide account roles."""

from uuid import UUID

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    BOARD_SETTING_FIELDS,
    Board,
    BoardMember,
    BoardMemberGrade,
    BoardMemberPatchForm,
    BoardPolicy,
    BoardSettingsPatchForm,
    ShelfPolicy,
)

STAFF = {"owner", "admin", "moderator"}


class BoardPermissionService:
    @staticmethod
    def check_read(board: Board, member: BoardMember | None) -> None:
        if board.status == "suspended" or (member is not None and member.board_id != board.id):
            raise BoardException(BoardErrorCode.NOT_FOUND)
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
        if board.status == "suspended" or (member and member.status in {"suspended", "banned"}):
            return False
        if policy is None or (action != "read_canvas" and board.status != "active"):
            return False
        if policy.board_id != board.id or (member is not None and member.board_id != board.id):
            return False
        if policy.audience == "public" and action == "read_canvas":
            return board.visibility == "public" or (
                member is not None and member.status == "active"
            )
        if member is None or member.status != "active":
            return False
        staff = member.role in STAFF
        if policy.staff_only:
            return staff
        if staff and policy.staff_bypass:
            return True
        own = grades.get(member.grade_id)
        minimum = grades.get(policy.min_grade_id)
        return (
            own is not None
            and minimum is not None
            and own.board_id == board.id
            and minimum.board_id == board.id
            and own.rank >= minimum.rank
        )

    def member_scope(self, board: Board, actor: BoardMember | None, *, audit: bool = False) -> str:
        self.check_read(board, actor)
        if actor is None or actor.status != "active":
            raise BoardException(BoardErrorCode.FORBIDDEN)
        if actor.role in {"owner", "admin"}:
            return "management"
        if actor.role == "moderator" and not audit:
            return "moderation"
        raise BoardException(BoardErrorCode.FORBIDDEN)

    def check_manage_grades(self, board: Board, actor: BoardMember | None) -> None:
        self.member_scope(board, actor, audit=True)
        if board.status != "active":
            raise BoardException(BoardErrorCode.FORBIDDEN)

    def check_invite(self, board: Board, actor: BoardMember | None) -> None:
        self.member_scope(board, actor, audit=True)
        if board.status != "active" or board.join_policy != "invite":
            raise BoardException(BoardErrorCode.FORBIDDEN)

    def check_settings_change(
        self, board: Board, actor: BoardMember | None, form: BoardSettingsPatchForm
    ) -> None:
        self.member_scope(board, actor, audit=True)
        fields = form.model_fields_set & set(BOARD_SETTING_FIELDS)
        owner = actor is not None and actor.role == "owner" and actor.user_id == board.owner_id
        if fields & {"visibility", "status"} and not owner:
            raise BoardException(BoardErrorCode.FORBIDDEN)
        if board.status == "archived" and not (
            owner
            and (form.status == "active" or (fields == {"status"} and form.status == "archived"))
        ):
            raise BoardException(BoardErrorCode.FORBIDDEN)

    def check_member_change(
        self, board: Board, actor: BoardMember, target: BoardMember, form: BoardMemberPatchForm
    ) -> None:
        self.member_scope(board, actor)
        if board.status != "active":
            raise BoardException(BoardErrorCode.FORBIDDEN)
        if (
            target.board_id != board.id
            or actor.user_id == target.user_id
            or target.role == "owner"
            or board.owner_id == target.user_id
            or target.status == "pending"
        ):
            raise BoardException(BoardErrorCode.FORBIDDEN)
        fields = form.model_fields_set & {"role", "status", "grade_id"}
        if actor.role == "admin" and (
            target.role not in {"member", "moderator"} or form.role == "admin"
        ):
            raise BoardException(BoardErrorCode.FORBIDDEN)
        if actor.role == "moderator" and (
            target.role != "member"
            or target.status != "active"
            or fields != {"status"}
            or form.status not in {"suspended", "banned"}
        ):
            raise BoardException(BoardErrorCode.FORBIDDEN)
        final_status = form.status if "status" in fields else target.status
        if "role" in fields and form.role != "member" and final_status != "active":
            raise BoardException(BoardErrorCode.INVALID_MEMBER_CHANGE)
