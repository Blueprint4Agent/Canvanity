"""Published Canvas reactions under current Board/Shelf policy."""

from uuid import UUID

from fastapi import Depends

from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.canvas import CanvasLikeResponse, CanvasRepository
from app.services.canvas_access import CanvasAccessService


class CanvasLikeService:
    def __init__(
        self,
        access: CanvasAccessService = Depends(),
        repository: CanvasRepository = Depends(),
    ):
        self.access = access
        self.repository = repository

    async def get(self, user_id: int | None, canvas_id: UUID) -> CanvasLikeResponse:
        async with self.repository.transaction(write=False) as tx:
            await self.access.read_context(
                tx, user_id, canvas_id, view="publication", metadata_only=True
            )
            return await tx.like_state(canvas_id, user_id)

    async def set(self, user_id: int, canvas_id: UUID, *, liked: bool) -> CanvasLikeResponse:
        async with self.repository.transaction() as tx:
            board, member, canvas, _ = await self.access.read_context(
                tx, user_id, canvas_id, view="publication", write=True, metadata_only=True
            )
            grades = {grade.id: grade for grade in await tx.board.grades(board.id)}
            policies, overrides = await tx.board.policy_rows(board.id)
            if not self.access.permissions.shelf_capabilities(
                board, member, canvas.shelf_id, grades, policies, overrides
            )["react"]:
                raise CanvasException(CanvasErrorCode.FORBIDDEN)
            await tx.set_like(canvas_id, user_id, liked=liked)
            return await tx.like_state(canvas_id, user_id)
