"""Board-local classification and policy use cases; all persistence stays in models/board.py."""

from uuid import UUID

from fastapi import Depends

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.core.error.shelf_exception import ShelfErrorCode, ShelfException
from app.models.board import (
    ACTIONS,
    MAX_BOARD_SHELVES,
    ActionPolicy,
    Board,
    BoardMember,
    BoardPoliciesForm,
    BoardPoliciesResponse,
    BoardPolicyActions,
    BoardRepository,
    BoardTransaction,
    PolicyChangeForm,
    Shelf,
    ShelfCreateForm,
    ShelfDetail,
    ShelfOrderForm,
    ShelfPatchForm,
    ShelfPoliciesForm,
    ShelfPoliciesResponse,
    ShelfPolicyActions,
    ShelfResponse,
    ShelvesResponse,
)
from app.services.board_permission import BoardPermissionService


class ShelfService:
    def __init__(
        self,
        permissions: BoardPermissionService = Depends(),
        repository: BoardRepository = Depends(),
    ):
        self.permissions = permissions
        self.repository = repository

    async def _board(
        self,
        tx: BoardTransaction,
        user_id: int | None,
        board_id: UUID,
        *,
        write: bool = False,
        manage: bool = False,
        expected_revision: int | None = None,
    ) -> tuple[Board, BoardMember | None]:
        board = await tx.locked_board(board_id) if write else await tx.read_board(board_id)
        if board is None:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        member = await tx.member(board.id, user_id) if user_id is not None else None
        self.permissions.check_read(board, member)
        if manage:
            self.permissions.check_manage_shelves(board, member, write=write)
        if expected_revision is not None and board.revision != expected_revision:
            raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
        return board, member

    async def _target(
        self,
        tx: BoardTransaction,
        user_id: int | None,
        shelf_id: UUID,
        *,
        write: bool = False,
        manage: bool = False,
        expected_revision: int | None = None,
    ) -> tuple[Board, BoardMember | None, Shelf, list[Shelf]]:
        board_id = await tx.shelf_board_id(shelf_id)
        if board_id is None:
            raise ShelfException(ShelfErrorCode.NOT_FOUND)
        try:
            board, member = await self._board(
                tx,
                user_id,
                board_id,
                write=write,
                manage=manage,
                expected_revision=expected_revision,
            )
        except BoardException as error:
            if error.code.error == BoardErrorCode.NOT_FOUND.code.error:
                raise ShelfException(ShelfErrorCode.NOT_FOUND) from None
            raise
        # Read again after the Board lock: another writer may have removed the shelf while waiting.
        shelves = await tx.shelves(board.id)
        shelf = next((s for s in shelves if s.id == shelf_id), None)
        if shelf is None:
            raise ShelfException(ShelfErrorCode.NOT_FOUND)
        return board, member, shelf, shelves

    async def _items(
        self, tx: BoardTransaction, board: Board, member: BoardMember | None, shelves: list[Shelf]
    ) -> list[ShelfDetail]:
        grades = {g.id: g for g in await tx.grades(board.id)}
        policies, overrides = await tx.policy_rows(board.id)
        return [
            ShelfDetail(
                id=s.id,
                board_id=s.board_id,
                slug=s.slug,
                name=s.name,
                description=s.description,
                icon=s.icon,
                purpose=s.purpose,
                classification=s.classification,
                sort_order=s.sort_order,
                is_default=s.is_default,
                is_visible=s.is_visible,
                capabilities=self.permissions.shelf_capabilities(
                    board, member, s.id, grades, policies, overrides
                ),
            )
            for s in shelves
        ]

    async def list(
        self, user_id: int | None, board_id: UUID, *, manage: bool = False
    ) -> ShelvesResponse:
        async with self.repository.transaction(write=False) as tx:
            board, member = await self._board(tx, user_id, board_id, manage=manage)
            items = await self._items(tx, board, member, await tx.shelves(board.id))
            if not manage:
                items = [s for s in items if s.is_visible and s.capabilities["read_canvas"]]
            return ShelvesResponse(items=items, board_revision=board.revision)

    async def get(self, user_id: int | None, shelf_id: UUID) -> ShelfResponse:
        async with self.repository.transaction(write=False) as tx:
            board, member, shelf, _ = await self._target(tx, user_id, shelf_id)
            item = (await self._items(tx, board, member, [shelf]))[0]
            if not item.capabilities["read_canvas"]:
                raise ShelfException(ShelfErrorCode.NOT_FOUND)
            return ShelfResponse(shelf=item, board_revision=board.revision)

    async def create(self, user_id: int, board_id: UUID, form: ShelfCreateForm) -> ShelfResponse:
        async with self.repository.transaction() as tx:
            board, member = await self._board(
                tx,
                user_id,
                board_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            shelves = await tx.shelves(board.id)
            if len(shelves) >= MAX_BOARD_SHELVES:
                raise ShelfException(ShelfErrorCode.LIMIT_REACHED)
            if any(s.slug == form.slug for s in shelves):
                raise ShelfException(ShelfErrorCode.SLUG_TAKEN)
            shelf = await tx.create_shelf(board, user_id, shelves, form)
            result = ShelfResponse(
                shelf=(await self._items(tx, board, member, [shelf]))[0],
                board_revision=board.revision,
            )
        return result

    async def change(self, user_id: int, shelf_id: UUID, form: ShelfPatchForm) -> ShelfResponse:
        async with self.repository.transaction() as tx:
            board, member, shelf, shelves = await self._target(
                tx,
                user_id,
                shelf_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            if form.slug is not None and any(
                s.id != shelf.id and s.slug == form.slug for s in shelves
            ):
                raise ShelfException(ShelfErrorCode.SLUG_TAKEN)
            await tx.change_shelf(board, user_id, shelf, form)
            result = ShelfResponse(
                shelf=(await self._items(tx, board, member, [shelf]))[0],
                board_revision=board.revision,
            )
        return result

    async def reorder(self, user_id: int, board_id: UUID, form: ShelfOrderForm) -> ShelvesResponse:
        async with self.repository.transaction() as tx:
            board, member = await self._board(
                tx,
                user_id,
                board_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            shelves = await tx.shelves(board.id)
            if set(form.shelf_ids) != {s.id for s in shelves}:
                raise ShelfException(ShelfErrorCode.INVALID_ORDER)
            ordered = await tx.reorder_shelves(board, user_id, shelves, form)
            result = ShelvesResponse(
                items=await self._items(tx, board, member, ordered), board_revision=board.revision
            )
        return result

    async def delete(self, user_id: int, shelf_id: UUID, form: PolicyChangeForm) -> int:
        async with self.repository.transaction() as tx:
            board, _, shelf, shelves = await self._target(
                tx,
                user_id,
                shelf_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            if shelf.is_default or len(shelves) == 1:
                raise ShelfException(ShelfErrorCode.PROTECTED)
            await tx.delete_shelf(board, user_id, shelf, form.reason)
            revision = board.revision
        return revision

    @staticmethod
    async def _validate_grades(
        tx: BoardTransaction, board: Board, actions: BoardPolicyActions | ShelfPolicyActions
    ) -> None:
        grades = {g.id for g in await tx.grades(board.id)}
        for action in ACTIONS:
            policy = getattr(actions, action)
            if (
                policy is not None
                and policy.min_grade_id is not None
                and policy.min_grade_id not in grades
            ):
                raise BoardException(BoardErrorCode.INVALID_GRADE)

    @staticmethod
    async def _policy_response(
        tx: BoardTransaction, board: Board, shelf_id: UUID | None
    ) -> BoardPoliciesResponse | ShelfPoliciesResponse:
        policies, overrides = await tx.policy_rows(board.id)
        if set(policies) != set(ACTIONS):
            raise BoardException(BoardErrorCode.UNAVAILABLE)
        base = {action: ActionPolicy.model_validate(policies[action]) for action in ACTIONS}
        if shelf_id is None:
            return BoardPoliciesResponse(
                board_id=board.id, actions=BoardPolicyActions(**base), board_revision=board.revision
            )
        custom = {
            action: ActionPolicy.model_validate(overrides[(shelf_id, action)])
            if (shelf_id, action) in overrides
            else None
            for action in ACTIONS
        }
        return ShelfPoliciesResponse(
            board_id=board.id,
            shelf_id=shelf_id,
            actions=ShelfPolicyActions(**custom),
            effective_actions=BoardPolicyActions(
                **{action: custom[action] or base[action] for action in ACTIONS}
            ),
            board_revision=board.revision,
        )

    async def board_policies(self, user_id: int, board_id: UUID) -> BoardPoliciesResponse:
        async with self.repository.transaction(write=False) as tx:
            board, _ = await self._board(tx, user_id, board_id, manage=True)
            return await self._policy_response(tx, board, None)

    async def set_board_policies(
        self, user_id: int, board_id: UUID, form: BoardPoliciesForm
    ) -> BoardPoliciesResponse:
        async with self.repository.transaction() as tx:
            board, _ = await self._board(
                tx,
                user_id,
                board_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            await self._validate_grades(tx, board, form.actions)
            await tx.replace_policies(board, user_id, None, form)
            result = await self._policy_response(tx, board, None)
        return result

    async def shelf_policies(self, user_id: int, shelf_id: UUID) -> ShelfPoliciesResponse:
        async with self.repository.transaction(write=False) as tx:
            board, _, shelf, _ = await self._target(tx, user_id, shelf_id, manage=True)
            return await self._policy_response(tx, board, shelf.id)

    async def set_shelf_policies(
        self, user_id: int, shelf_id: UUID, form: ShelfPoliciesForm
    ) -> ShelfPoliciesResponse:
        async with self.repository.transaction() as tx:
            board, _, shelf, _ = await self._target(
                tx,
                user_id,
                shelf_id,
                write=True,
                manage=True,
                expected_revision=form.expected_revision,
            )
            if shelf.purpose == "notice" and any(
                getattr(form.actions, action) is None
                or not getattr(form.actions, action).staff_only
                for action in ("create_canvas", "create_comment")
            ):
                raise ShelfException(ShelfErrorCode.INVALID_POLICY)
            await self._validate_grades(tx, board, form.actions)
            await tx.replace_policies(board, user_id, shelf.id, form)
            result = await self._policy_response(tx, board, shelf.id)
        return result
