"""Membership policies use the model Repository's locked aggregate transaction."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    GRADE_AUDIT_ACTIONS,
    MAX_BOARD_USER_ID,
    BoardAuditPageResponse,
    BoardAuditQuery,
    BoardAuditState,
    BoardGradeAuditChange,
    BoardMemberAuditResponse,
    BoardMemberData,
    BoardMemberDetail,
    BoardMemberListResponse,
    BoardMemberPatchForm,
    BoardMemberPublic,
    BoardMembersQuery,
    BoardMemberUpdateResponse,
    BoardRepository,
    MembershipSummary,
)
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

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _context(*values) -> str:
        return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()

    @classmethod
    def _cursor(cls, timestamp: datetime, record_id, context: str) -> str:
        data = {
            "version": 1,
            "at": cls._utc(timestamp).isoformat(),
            "id": str(record_id),
            "context": context,
        }
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    @classmethod
    def _before(cls, cursor: str | None, context: str, *, audit: bool = False):
        if cursor is None:
            return None
        try:
            if not cursor or len(cursor) > 2048:
                raise ValueError("Invalid cursor length")
            data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
            if (
                data["version"] != 1
                or data["context"] != context
                or not isinstance(data["id"], str)
            ):
                raise ValueError("Cursor context mismatch")
            timestamp = datetime.fromisoformat(data["at"])
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("Cursor timestamp requires timezone")
            record_id = UUID(data["id"]) if audit else int(data["id"])
            if not audit and (
                not 0 < record_id <= MAX_BOARD_USER_ID or str(record_id) != data["id"]
            ):
                raise ValueError("Invalid member id")
            return cls._utc(timestamp), record_id
        except (ValueError, KeyError, TypeError, UnicodeError, OverflowError):
            raise BoardException(BoardErrorCode.INVALID_CURSOR) from None

    @classmethod
    def _detail(cls, data: BoardMemberData) -> BoardMemberDetail:
        return BoardMemberDetail(
            user_id=data.member.user_id,
            name=data.name,
            handle=data.handle,
            role=data.member.role,
            status=data.member.status,
            grade_id=data.grade.id,
            grade_name=data.grade.name,
            grade_rank=data.grade.rank,
            joined_at=cls._utc(data.member.joined_at),
        )

    async def members(
        self, user_id: int, board_id: UUID, query: BoardMembersQuery
    ) -> BoardMemberListResponse:
        async with self.repository.transaction(write=False) as tx:
            board = await tx.read_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            actor = await tx.member(board_id, user_id)
            scope = self.permissions.member_scope(board, actor)
            context = self._context(
                "members", str(board_id), user_id, scope, query.q.strip(), query.role, query.status
            )
            rows = await tx.list_members(
                board_id,
                query,
                moderation_only=scope == "moderation",
                before=self._before(query.cursor, context),
            )
            items = [
                self._detail(row)
                if scope == "management"
                else BoardMemberPublic(user_id=row.member.user_id, name=row.name, handle=row.handle)
                for row in rows[: query.limit]
            ]
            cursor = (
                self._cursor(
                    rows[query.limit - 1].member.joined_at,
                    rows[query.limit - 1].member.user_id,
                    context,
                )
                if len(rows) > query.limit
                else None
            )
            return BoardMemberListResponse(
                scope=scope, items=items, next_cursor=cursor, board_revision=board.revision
            )

    async def change_member(
        self, user_id: int, board_id: UUID, target_user_id: int, form: BoardMemberPatchForm
    ) -> BoardMemberUpdateResponse:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            actor = await tx.member(board_id, user_id)
            self.permissions.member_scope(board, actor)
            if board.status != "active":
                raise BoardException(BoardErrorCode.FORBIDDEN)
            if board.revision != form.expected_revision:
                raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
            if not 0 < target_user_id <= MAX_BOARD_USER_ID:
                raise BoardException(BoardErrorCode.MEMBER_NOT_FOUND)
            target = await tx.member_details(board_id, target_user_id)
            if target is None:
                raise BoardException(BoardErrorCode.MEMBER_NOT_FOUND)
            self.permissions.check_member_change(board, actor, target.member, form)
            if "grade_id" in form.model_fields_set:
                grade = await tx.grade(form.grade_id)
                if grade is None or grade.board_id != board_id:
                    raise BoardException(BoardErrorCode.INVALID_GRADE)
            updated = await tx.update_member(board, target.member, user_id, form)
            result = BoardMemberUpdateResponse(
                member=self._detail(updated), board_revision=board.revision
            )
        return result

    @classmethod
    def _audit_entry(cls, row) -> BoardMemberAuditResponse:
        changes = row.changes
        before = changes.get("before")
        after = changes.get("after")
        if row.action in {"board_created", "member_joined"}:
            after = changes
        elif row.action == "member_left":
            before = {key: changes.get("previous_" + key) for key in ("role", "status", "grade_id")}

        def state(value):
            return BoardAuditState.model_validate(value) if isinstance(value, dict) else None

        return BoardMemberAuditResponse(
            id=row.id,
            actor_user_id=row.actor_user_id,
            target_user_id=row.target_user_id,
            action=row.action,
            before=state(before),
            after=state(after),
            reason=changes.get("reason"),
            grade_change=(
                BoardGradeAuditChange.model_validate(changes)
                if row.action in GRADE_AUDIT_ACTIONS
                else None
            ),
            created_at=cls._utc(row.created_at),
        )

    async def member_audit(
        self, user_id: int, board_id: UUID, query: BoardAuditQuery
    ) -> BoardAuditPageResponse:
        async with self.repository.transaction(write=False) as tx:
            board = await tx.read_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            actor = await tx.member(board_id, user_id)
            self.permissions.member_scope(board, actor, audit=True)
            try:
                if query.since.tzinfo is None or query.until.tzinfo is None:
                    raise ValueError("Timezone required")
                since, until = self._utc(query.since), self._utc(query.until)
                if not timedelta(0) < until - since <= timedelta(days=180):
                    raise ValueError("Invalid audit period")
            except (ValueError, OverflowError):
                raise BoardException(BoardErrorCode.INVALID_AUDIT_WINDOW) from None
            normalized = query.model_copy(update={"since": since, "until": until})
            context = self._context(
                "audit",
                str(board_id),
                user_id,
                since.isoformat(),
                until.isoformat(),
                query.target_user_id,
            )
            rows = await tx.list_member_audit(
                board_id, normalized, before=self._before(query.cursor, context, audit=True)
            )
            cursor = (
                self._cursor(rows[query.limit - 1].created_at, rows[query.limit - 1].id, context)
                if len(rows) > query.limit
                else None
            )
            return BoardAuditPageResponse(
                items=[self._audit_entry(row) for row in rows[: query.limit]],
                next_cursor=cursor,
                board_revision=board.revision,
            )
