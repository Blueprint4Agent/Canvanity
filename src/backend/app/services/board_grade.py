"""Board-local grade settings, independent of operational roles."""

from uuid import UUID

from fastapi import Depends

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    MAX_BOARD_GRADES,
    Board,
    BoardGradeCreateForm,
    BoardGradeDeleteForm,
    BoardGradeOrderForm,
    BoardGradePatchForm,
    BoardGradeResponse,
    BoardGradesResponse,
    BoardMemberGrade,
    BoardRepository,
    BoardTransaction,
    GradeSummary,
)
from app.services.board_permission import BoardPermissionService


class BoardGradeService:
    def __init__(
        self,
        permissions: BoardPermissionService = Depends(),
        repository: BoardRepository = Depends(),
    ):
        self.permissions = permissions
        self.repository = repository

    @staticmethod
    def _summary(grade: BoardMemberGrade) -> GradeSummary:
        return GradeSummary(
            id=grade.id, name=grade.name, rank=grade.rank, is_default=grade.is_default
        )

    @classmethod
    def _list_response(cls, board: Board, grades: list[BoardMemberGrade]) -> BoardGradesResponse:
        return BoardGradesResponse(
            items=[cls._summary(g) for g in sorted(grades, key=lambda g: (g.rank, g.id))],
            board_revision=board.revision,
        )

    @staticmethod
    def _grade(grades: list[BoardMemberGrade], grade_id: UUID) -> BoardMemberGrade:
        grade = next((g for g in grades if g.id == grade_id), None)
        if grade is None:
            raise BoardException(BoardErrorCode.GRADE_NOT_FOUND)
        return grade

    async def _locked(
        self, tx: BoardTransaction, user_id: int, board_id: UUID, expected_revision: int
    ) -> Board:
        board = await tx.locked_board(board_id)
        if board is None:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        actor = await tx.member(board_id, user_id)
        self.permissions.check_manage_grades(board, actor)
        if board.revision != expected_revision:
            raise BoardException(BoardErrorCode.CONFLICT, {"current_revision": board.revision})
        return board

    async def list(self, user_id: int | None, board_id: UUID) -> BoardGradesResponse:
        async with self.repository.transaction(write=False) as tx:
            data = await tx.grade_listing(board_id, user_id)
            if data is None:
                raise BoardException(BoardErrorCode.NOT_FOUND)
            self.permissions.check_read(data.board, data.member)
            return self._list_response(data.board, data.grades)

    async def create(
        self, user_id: int, board_id: UUID, form: BoardGradeCreateForm
    ) -> BoardGradeResponse:
        async with self.repository.transaction() as tx:
            board = await self._locked(tx, user_id, board_id, form.expected_revision)
            grades = await tx.grades(board_id)
            if len(grades) >= MAX_BOARD_GRADES:
                raise BoardException(BoardErrorCode.GRADE_LIMIT_REACHED)
            if any(g.name == form.name for g in grades):
                raise BoardException(BoardErrorCode.GRADE_NAME_TAKEN)
            if any(g.rank == form.rank for g in grades):
                raise BoardException(BoardErrorCode.GRADE_RANK_TAKEN)
            grade = await tx.create_grade(board, user_id, grades, form)
            result = BoardGradeResponse(grade=self._summary(grade), board_revision=board.revision)
        return result

    async def change(
        self, user_id: int, board_id: UUID, grade_id: UUID, form: BoardGradePatchForm
    ) -> BoardGradeResponse:
        async with self.repository.transaction() as tx:
            board = await self._locked(tx, user_id, board_id, form.expected_revision)
            grades = await tx.grades(board_id)
            grade = self._grade(grades, grade_id)
            if form.name is not None and any(
                g.id != grade_id and g.name == form.name for g in grades
            ):
                raise BoardException(BoardErrorCode.GRADE_NAME_TAKEN)
            grade = await tx.change_grade(board, user_id, grades, grade, form)
            result = BoardGradeResponse(grade=self._summary(grade), board_revision=board.revision)
        return result

    async def reorder(
        self, user_id: int, board_id: UUID, form: BoardGradeOrderForm
    ) -> BoardGradesResponse:
        async with self.repository.transaction() as tx:
            board = await self._locked(tx, user_id, board_id, form.expected_revision)
            grades = await tx.grades(board_id)
            if set(form.grade_ids) != {g.id for g in grades}:
                raise BoardException(BoardErrorCode.INVALID_GRADE_ORDER)
            ordered = await tx.reorder_grades(board, user_id, grades, form)
            result = self._list_response(board, ordered)
        return result

    async def delete(
        self, user_id: int, board_id: UUID, grade_id: UUID, form: BoardGradeDeleteForm
    ) -> BoardGradesResponse:
        async with self.repository.transaction() as tx:
            board = await self._locked(tx, user_id, board_id, form.expected_revision)
            grades = await tx.grades(board_id)
            grade = self._grade(grades, grade_id)
            if len(grades) == 1:
                raise BoardException(BoardErrorCode.LAST_GRADE)
            replacement = next((g for g in grades if g.id == form.replacement_grade_id), None)
            if replacement is None or replacement.id == grade.id:
                raise BoardException(BoardErrorCode.INVALID_GRADE)
            remaining = await tx.delete_grade(board, user_id, grades, grade, replacement, form)
            result = self._list_response(board, remaining)
        return result
