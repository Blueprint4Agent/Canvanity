"""Board application policies and orchestration; persistence belongs to the model Repository."""

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.error import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    ACTIONS,
    Board,
    BoardCreateForm,
    BoardDeleteForm,
    BoardHomeResponse,
    BoardPageResponse,
    BoardRepository,
    BoardSummary,
    GradeSummary,
    MembershipSummary,
    ShelfSummary,
)
from app.services.board_permission import BoardPermissionService


class BoardService:
    def __init__(
        self,
        permissions: Annotated[BoardPermissionService, Depends()],
        repository: Annotated[BoardRepository, Depends()],
    ):
        self.permissions = permissions
        self.repository = repository

    async def create(self, user_id: int, form: BoardCreateForm) -> BoardSummary:
        async with self.repository.transaction(create_slug=form.slug) as tx:
            if not await tx.lock_creator(user_id):
                raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
            if await tx.owned_count(user_id) >= 20:
                raise BoardException(BoardErrorCode.LIMIT_REACHED)
            if await tx.slug_exists(form.slug):
                raise BoardException(BoardErrorCode.SLUG_TAKEN)
            by_slug = await tx.active_interests(form.interest_ids)
            if len(by_slug) != len(form.interest_ids):
                raise BoardException(BoardErrorCode.INVALID_INTEREST)
            board = await tx.create_board(user_id, form)
            await tx.initialize(board, user_id, [by_slug[key].id for key in form.interest_ids])
            result = self._summary(board, form.interest_ids)
        return result

    @staticmethod
    def _summary(board: Board, interests: list[str]) -> BoardSummary:
        created = board.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return BoardSummary(
            id=board.id,
            owner_id=board.owner_id,
            slug=board.slug,
            name=board.name,
            description=board.description,
            visibility=board.visibility,
            join_policy=board.join_policy,
            status=board.status,
            revision=board.revision,
            interest_ids=interests,
            created_at=created,
        )

    async def list(
        self,
        user_id: int | None,
        *,
        limit: int,
        cursor: str | None,
        q: str,
        interest_id: str | None,
        mine: bool,
    ) -> BoardPageResponse:
        if mine and user_id is None:
            raise AuthException(code=AuthErrorCode.INVALID_TOKEN)
        fingerprint = hashlib.sha256(
            json.dumps([q, interest_id, mine], ensure_ascii=False).encode()
        ).hexdigest()
        before = None
        if cursor:
            try:
                decoded = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                created = datetime.fromisoformat(decoded["created_at"])
                last_id = UUID(decoded["id"])
                if (
                    created.tzinfo is None
                    or decoded["filter"] != fingerprint
                    or decoded["version"] != 1
                ):
                    raise ValueError("Cursor does not match the query.")
                before = (created, last_id)
            except (ValueError, KeyError, TypeError, UnicodeError):
                raise BoardException(BoardErrorCode.INVALID_CURSOR) from None
        boards, interests = await self.repository.list_visible(
            user_id, limit=limit, q=q, interest_id=interest_id, mine=mine, before=before
        )
        items = [self._summary(board, interests[board.id]) for board in boards[:limit]]
        next_cursor = None
        if len(boards) > limit:
            last = items[-1]
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "version": 1,
                            "created_at": last.created_at.isoformat(),
                            "id": str(last.id),
                            "filter": fingerprint,
                        }
                    ).encode()
                )
                .decode()
                .rstrip("=")
            )
        return BoardPageResponse(items=items, next_cursor=next_cursor)

    async def home(
        self, user_id: int | None, *, board_id: UUID | None = None, slug: str | None = None
    ) -> BoardHomeResponse:
        data = await self.repository.home_data(user_id, board_id=board_id, slug=slug)
        if data is None:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        board, member = data.board, data.member
        self.permissions.check_read(board, member)
        by_id = {grade.id: grade for grade in data.grades}
        shelves = []
        for shelf in data.shelves:
            capabilities = {
                action: self.permissions.allowed(
                    board,
                    member,
                    data.overrides.get((shelf.id, action), data.policies.get(action)),
                    by_id,
                    action,
                )
                for action in ACTIONS
            }
            if capabilities["read_canvas"]:
                shelves.append(
                    ShelfSummary(
                        id=shelf.id,
                        slug=shelf.slug,
                        name=shelf.name,
                        description=shelf.description,
                        icon=shelf.icon,
                        purpose=shelf.purpose,
                        classification=shelf.classification,
                        sort_order=shelf.sort_order,
                        is_default=shelf.is_default,
                        capabilities=capabilities,
                    )
                )
        if data.layout is None:
            raise BoardException(BoardErrorCode.UNAVAILABLE)
        membership = (
            MembershipSummary(
                role=member.role,
                status=member.status,
                grade_id=member.grade_id,
                grade_name=by_id[member.grade_id].name,
            )
            if member
            else None
        )
        return BoardHomeResponse(
            board=self._summary(board, data.interests),
            rules=board.rules,
            membership=membership,
            grades=[
                GradeSummary(id=g.id, name=g.name, rank=g.rank, is_default=g.is_default)
                for g in data.grades
            ],
            shelves=shelves,
            layout=data.layout.document,
            layout_revision=data.layout.revision,
        )

    async def delete_empty(self, user_id: int, board_id: UUID, form: BoardDeleteForm) -> None:
        async with self.repository.transaction(deleting=True) as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            member = await tx.member(board_id, user_id)
            self.permissions.check_read(board, member)
            if (
                board.owner_id != user_id
                or member is None
                or member.role != "owner"
                or member.status != "active"
                or board.status == "suspended"
            ):
                raise BoardException(BoardErrorCode.FORBIDDEN)
            if board.revision != form.expected_revision:
                raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
            if board.slug != form.confirm_slug:
                raise BoardException(BoardErrorCode.DELETE_CONFIRMATION)
            if await tx.member_count(board_id) != 1:
                raise BoardException(BoardErrorCode.NOT_EMPTY)
            await tx.delete_board(board)
