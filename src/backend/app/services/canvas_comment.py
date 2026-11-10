"""Current publication policy and author/moderator comment use cases."""

import base64
import binascii
import json
import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends

from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import BOARD_STAFF_ROLES
from app.models.canvas import MAX_CANVAS_REVISION, as_utc
from app.models.canvas_comment import (
    CommentCapabilities,
    CommentCreateForm,
    CommentPage,
    CommentPatchForm,
    CommentQuery,
    CommentRepository,
    CommentResponse,
    CommentRevisionForm,
)
from app.services.canvas_access import CanvasAccessService
from app.services.canvas_feed import unique_json_object


class CanvasCommentService:
    def __init__(
        self, access: CanvasAccessService = Depends(), repository: CommentRepository = Depends()
    ):
        self.access, self.repository = access, repository

    async def _context(self, tx, user_id, canvas_id, *, write=False):
        board, member, canvas, _ = await self.access.read_context(
            tx, user_id, canvas_id, view="publication", write=write, metadata_only=True
        )
        grades = {grade.id: grade for grade in await tx.board.grades(board.id)}
        policies, overrides = await tx.board.policy_rows(board.id)
        can_create = self.access.permissions.shelf_capabilities(
            board, member, canvas.shelf_id, grades, policies, overrides
        )["create_comment"]
        staff = (
            member is not None and member.status == "active" and member.role in BOARD_STAFF_ROLES
        )
        can_manage = board.status == "active" and member is not None and member.status == "active"
        return can_create, staff, can_manage

    @staticmethod
    def _response(row, user_id, *, can_create, staff, can_manage):
        own = user_id is not None and row.author_id == user_id
        return CommentResponse(
            id=row.id,
            canvas_id=row.canvas_id,
            author_id=row.author_id,
            body=None if row.status == "deleted" else row.body,
            status=row.status,
            revision=row.revision,
            created_at=as_utc(row.created_at),
            updated_at=as_utc(row.updated_at),
            capabilities=CommentCapabilities(
                edit=own and can_create and row.status == "visible",
                delete=can_manage and (own or staff) and row.status != "deleted",
                moderate=can_manage and staff and row.status != "deleted",
            ),
        )

    @staticmethod
    def _before(value, context):
        if value is None:
            return None
        try:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
                raise ValueError("Invalid cursor.")
            raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
            if base64.urlsafe_b64encode(raw).decode().rstrip("=") != value:
                raise ValueError("Non-canonical cursor.")
            data = json.loads(raw, object_pairs_hook=unique_json_object)
            if (
                not isinstance(data, dict)
                or set(data) != {"v", "context", "at", "id"}
                or type(data["v"]) is not int
                or data["v"] != 1
                or data["context"] != context
            ):
                raise ValueError("Cursor context changed.")
            at = datetime.fromisoformat(data["at"])
            if at.tzinfo is None or at.utcoffset().total_seconds() != 0:
                raise ValueError("UTC cursor required.")
            return at, UUID(data["id"])
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, binascii.Error):
            raise CanvasException(CanvasErrorCode.INVALID_CURSOR) from None

    async def list(self, user_id: int | None, canvas_id: UUID, query: CommentQuery) -> CommentPage:
        context = f"comments:{canvas_id}:{user_id}:{query.status}"
        before = self._before(query.cursor, context)
        async with self.repository.transaction(write=False) as tx:
            can_create, staff, can_manage = await self._context(tx, user_id, canvas_id)
            if query.status == "all" and not staff:
                raise CanvasException(CanvasErrorCode.FORBIDDEN)
            rows = await tx.comments(canvas_id, query, before)
            cursor = None
            if len(rows) > query.limit:
                last = rows[query.limit - 1]
                payload = {
                    "v": 1,
                    "context": context,
                    "at": as_utc(last.created_at).astimezone(UTC).isoformat(),
                    "id": str(last.id),
                }
                cursor = (
                    base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
                    .decode()
                    .rstrip("=")
                )
            return CommentPage(
                items=[
                    self._response(
                        row, user_id, can_create=can_create, staff=staff, can_manage=can_manage
                    )
                    for row in rows[: query.limit]
                ],
                next_cursor=cursor,
                can_create=can_create,
            )

    async def get(self, user_id: int | None, canvas_id: UUID, comment_id: UUID) -> CommentResponse:
        async with self.repository.transaction(write=False) as tx:
            can_create, staff, can_manage = await self._context(tx, user_id, canvas_id)
            row = await tx.comment(canvas_id, comment_id)
            if row is None or (
                row.status == "hidden"
                and not staff
                and not (user_id is not None and row.author_id == user_id)
            ):
                raise CanvasException(CanvasErrorCode.NOT_FOUND)
            return self._response(
                row, user_id, can_create=can_create, staff=staff, can_manage=can_manage
            )

    async def create(
        self, user_id: int, canvas_id: UUID, form: CommentCreateForm
    ) -> CommentResponse:
        async with self.repository.transaction() as tx:
            can_create, staff, can_manage = await self._context(tx, user_id, canvas_id, write=True)
            if not can_create:
                raise CanvasException(CanvasErrorCode.FORBIDDEN)
            row = await tx.add_comment(canvas_id, user_id, form.body)
            return self._response(
                row, user_id, can_create=can_create, staff=staff, can_manage=can_manage
            )

    async def change(
        self,
        user_id: int,
        canvas_id: UUID,
        comment_id: UUID,
        form: CommentPatchForm | CommentRevisionForm,
        *,
        delete=False,
    ) -> CommentResponse:
        async with self.repository.transaction() as tx:
            can_create, staff, can_manage = await self._context(tx, user_id, canvas_id, write=True)
            row = await tx.comment(canvas_id, comment_id)
            if row is None:
                raise CanvasException(CanvasErrorCode.NOT_FOUND)
            own = row.author_id == user_id
            if delete:
                allowed = can_manage and (own or staff)
                body, status, reason = None, "deleted", None
            else:
                body, status, reason = form.body, form.status, form.reason
                allowed = (
                    (own and can_create and row.status == "visible")
                    if body is not None
                    else (can_manage and staff and row.status != "deleted")
                )
            if not allowed:
                raise CanvasException(CanvasErrorCode.FORBIDDEN)
            if row.revision != form.expected_revision:
                raise CanvasException(
                    CanvasErrorCode.COMMENT_CONFLICT, {"current_revision": row.revision}
                )
            if (body is not None and body != row.body) or (
                status is not None and status != row.status
            ):
                if row.revision >= MAX_CANVAS_REVISION:
                    raise CanvasException(
                        CanvasErrorCode.COMMENT_CONFLICT, {"current_revision": row.revision}
                    )
                await tx.change_comment(
                    row, body=body, status=status, actor_id=user_id, reason=reason
                )
            return self._response(
                row, user_id, can_create=can_create, staff=staff, can_manage=can_manage
            )
