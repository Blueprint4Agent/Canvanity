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
    Board,
    BoardCreateForm,
    BoardDeleteForm,
    BoardHomeResponse,
    BoardOwnershipTransferForm,
    BoardOwnershipTransferResponse,
    BoardPageResponse,
    BoardRepository,
    BoardSettingsPatchForm,
    BoardSummary,
    BoardUpdateResponse,
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

    async def update(
        self, user_id: int, board_id: UUID, form: BoardSettingsPatchForm
    ) -> BoardUpdateResponse:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            actor = await tx.member(board_id, user_id)
            self.permissions.check_settings_change(board, actor, form)
            if board.revision != form.expected_revision:
                raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
            visibility = form.visibility or board.visibility
            join_policy = form.join_policy or board.join_policy
            if visibility == "private" and (
                join_policy != "invite"
                or (board.visibility == "public" and form.join_policy != "invite")
            ):
                raise BoardException(BoardErrorCode.INVALID_SETTINGS)
            interests = None
            if form.interest_ids is not None:
                by_slug = await tx.active_interests(form.interest_ids)
                if len(by_slug) != len(form.interest_ids):
                    raise BoardException(BoardErrorCode.INVALID_INTEREST)
                interests = [by_slug[slug] for slug in form.interest_ids]
            slugs = await tx.update_settings(board, user_id, form, interests)
            result = BoardUpdateResponse(
                board=self._summary(board, slugs), rules=board.rules, board_revision=board.revision
            )
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
            capabilities = self.permissions.shelf_capabilities(
                board, member, shelf.id, by_id, data.policies, data.overrides
            )
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

    async def transfer_ownership(
        self, user_id: int, board_id: UUID, form: BoardOwnershipTransferForm
    ) -> BoardOwnershipTransferResponse:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            owner = await tx.member(board_id, user_id)
            self.permissions.check_owner_action(board, owner)
            if board.revision != form.expected_revision:
                raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
            target = await tx.member(board_id, form.target_user_id)
            if (
                target is None
                or target.user_id == user_id
                or target.status != "active"
                or target.role == "owner"
            ):
                raise BoardException(BoardErrorCode.INVALID_OWNERSHIP_TARGET)
            if not await tx.lock_active_user(target.user_id):
                raise BoardException(BoardErrorCode.INVALID_OWNERSHIP_TARGET)
            await tx.transfer_ownership(board, owner, target, form.reason)
            result = BoardOwnershipTransferResponse(
                board_id=board_id,
                previous_owner_id=user_id,
                owner_id=target.user_id,
                board_revision=board.revision,
            )
        return result

    async def delete_board(self, user_id: int, board_id: UUID, form: BoardDeleteForm) -> None:
        async with self.repository.transaction(deleting=True) as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            member = await tx.member(board_id, user_id)
            self.permissions.check_owner_action(board, member)
            if board.revision != form.expected_revision:
                raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
            if board.slug != form.confirm_slug:
                raise BoardException(BoardErrorCode.DELETE_CONFIRMATION)
            if board.status != "archived" and (
                await tx.member_count(board_id) != 1 or await tx.canvas_count(board_id)
            ):
                raise BoardException(BoardErrorCode.NOT_EMPTY)
            await tx.delete_board(board)
