"""Official layout management uses the current Board role under aggregate locks."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError

from app.core.error import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import BoardRepository
from app.models.board_layout import BoardLayoutDocument, BoardLayoutResponse, BoardLayoutSaveForm
from app.services.board_permission import BoardPermissionService


class BoardLayoutService:
    def __init__(
        self,
        permissions: Annotated[BoardPermissionService, Depends()],
        repository: Annotated[BoardRepository, Depends()],
    ):
        self.permissions = permissions
        self.repository = repository

    async def get(self, user_id: int, board_id: UUID) -> BoardLayoutResponse:
        return await self._manage(user_id, board_id, None)

    async def save(
        self, user_id: int, board_id: UUID, form: BoardLayoutSaveForm
    ) -> BoardLayoutResponse:
        return await self._manage(user_id, board_id, form)

    async def _manage(
        self, user_id: int, board_id: UUID, form: BoardLayoutSaveForm | None
    ) -> BoardLayoutResponse:
        async with self.repository.transaction() as tx:
            board = await tx.locked_board(board_id)
            if board is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            if not await tx.lock_active_user(user_id):
                raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
            actor = await tx.member(board_id, user_id)
            self.permissions.check_manage_structure(board, actor, write=form is not None)
            layout = await tx.layout(board_id)
            if layout is None:
                raise BoardException(BoardErrorCode.UNAVAILABLE)
            if form is not None:
                # Reject stale saves first, even when their document is unchanged or invalid in scope.
                if layout.revision != form.expected_revision:
                    raise BoardException(
                        BoardErrorCode.LAYOUT_CONFLICT, {"current_revision": layout.revision}
                    )
                shelves = await tx.layout_source_shelves(board_id)
                for widget in form.document.widgets:
                    if widget.type == "canvas_collection" and (
                        widget.source.board_id != board_id
                        or (
                            widget.source.shelf_id is not None
                            and widget.source.shelf_id not in shelves
                        )
                    ):
                        raise BoardException(BoardErrorCode.INVALID_LAYOUT_SOURCE)
                await tx.save_layout(layout, user_id, form)
            try:
                document = BoardLayoutDocument.model_validate(layout.document)
            except ValidationError as error:
                raise BoardException(BoardErrorCode.UNAVAILABLE) from error
            result = BoardLayoutResponse(
                board_id=board_id, document=document, layout_revision=layout.revision
            )
        return result
