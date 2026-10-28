from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.error.board_exception import BoardErrorCode, board_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user, get_current_token_user
from app.models.board import (
    BoardAuditPageResponse,
    BoardAuditQuery,
    BoardCreateForm,
    BoardDeleteForm,
    BoardGradeCreateForm,
    BoardGradeDeleteForm,
    BoardGradeOrderForm,
    BoardGradePatchForm,
    BoardGradeResponse,
    BoardGradesResponse,
    BoardHomeResponse,
    BoardMemberListResponse,
    BoardMemberPatchForm,
    BoardMembersQuery,
    BoardMemberUpdateResponse,
    BoardPageResponse,
    BoardSummary,
    MembershipSummary,
)
from app.models.user import UserResponse
from app.services.board import BoardService
from app.services.board_grade import BoardGradeService
from app.services.board_membership import BoardMembershipService

router = APIRouter()
READ_ERRORS = current_user_error_responses(
    board_error_responses(BoardErrorCode.NOT_FOUND, BoardErrorCode.UNAVAILABLE)
)


@router.get(
    "",
    openapi_extra={"security": [{}]},
    response_model=BoardPageResponse,
    responses=current_user_error_responses(board_error_responses(BoardErrorCode.INVALID_CURSOR)),
)
async def list_boards(
    response: Response,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=2048),
    q: str = Query(default="", max_length=200),
    interest_id: str | None = Query(default=None, max_length=40),
    mine: bool = False,
    user: UserResponse | None = Depends(get_current_token_user),
    service: BoardService = Depends(),
) -> BoardPageResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(
        user.id if user else None,
        limit=limit,
        cursor=cursor,
        q=q.strip(),
        interest_id=interest_id,
        mine=mine,
    )


@router.post(
    "",
    response_model=BoardSummary,
    status_code=status.HTTP_201_CREATED,
    responses=current_user_error_responses(
        board_error_responses(
            BoardErrorCode.SLUG_TAKEN,
            BoardErrorCode.LIMIT_REACHED,
            BoardErrorCode.INVALID_INTEREST,
            BoardErrorCode.UNAVAILABLE,
        )
    ),
)
async def create_board(
    form: BoardCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardService = Depends(),
) -> BoardSummary:
    board = await service.create(user.id, form)
    response.headers["Location"] = f"/api/v1/boards/{board.id}"
    response.headers["Cache-Control"] = "private, no-store"
    return board


@router.get(
    "/by-slug/{slug}",
    openapi_extra={"security": [{}]},
    response_model=BoardHomeResponse,
    responses=READ_ERRORS,
)
async def home_by_slug(
    slug: str,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: BoardService = Depends(),
) -> BoardHomeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.home(user.id if user else None, slug=slug)


@router.get(
    "/{board_id}",
    openapi_extra={"security": [{}]},
    response_model=BoardHomeResponse,
    responses=READ_ERRORS,
)
@router.get(
    "/{board_id}/home",
    openapi_extra={"security": [{}]},
    response_model=BoardHomeResponse,
    responses=READ_ERRORS,
)
async def board_home(
    board_id: UUID,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: BoardService = Depends(),
) -> BoardHomeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.home(user.id if user else None, board_id=board_id)


@router.delete(
    "/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=current_user_error_responses(
        board_error_responses(
            BoardErrorCode.NOT_FOUND,
            BoardErrorCode.FORBIDDEN,
            BoardErrorCode.CONFLICT,
            BoardErrorCode.DELETE_CONFIRMATION,
            BoardErrorCode.NOT_EMPTY,
            BoardErrorCode.UNAVAILABLE,
        )
    ),
)
async def delete_empty_board(
    board_id: UUID,
    form: BoardDeleteForm,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardService = Depends(),
) -> None:
    await service.delete_empty(user.id, board_id, form)


MEMBERSHIP_ERRORS = current_user_error_responses(
    board_error_responses(
        BoardErrorCode.NOT_FOUND, BoardErrorCode.FORBIDDEN, BoardErrorCode.UNAVAILABLE
    )
)


@router.post("/{board_id}/join", response_model=MembershipSummary, responses=MEMBERSHIP_ERRORS)
async def join_board(
    board_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMembershipService = Depends(),
) -> MembershipSummary:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.join(user.id, board_id)


@router.delete(
    "/{board_id}/membership",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=current_user_error_responses(
        board_error_responses(
            BoardErrorCode.NOT_FOUND,
            BoardErrorCode.FORBIDDEN,
            BoardErrorCode.OWNER_CANNOT_LEAVE,
            BoardErrorCode.UNAVAILABLE,
        )
    ),
)
async def leave_board(
    board_id: UUID,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMembershipService = Depends(),
) -> None:
    await service.leave(user.id, board_id)


GRADE_WRITE_CODES = (
    BoardErrorCode.NOT_FOUND,
    BoardErrorCode.FORBIDDEN,
    BoardErrorCode.CONFLICT,
    BoardErrorCode.UNAVAILABLE,
)


@router.get(
    "/{board_id}/grades",
    openapi_extra={"security": [{}]},
    response_model=BoardGradesResponse,
    responses=READ_ERRORS,
)
async def grades(
    board_id: UUID,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: BoardGradeService = Depends(),
) -> BoardGradesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(user.id if user else None, board_id)


@router.post(
    "/{board_id}/grades",
    status_code=status.HTTP_201_CREATED,
    response_model=BoardGradeResponse,
    responses=current_user_error_responses(
        board_error_responses(
            *GRADE_WRITE_CODES,
            BoardErrorCode.GRADE_LIMIT_REACHED,
            BoardErrorCode.GRADE_NAME_TAKEN,
            BoardErrorCode.GRADE_RANK_TAKEN,
        )
    ),
)
async def create_grade(
    board_id: UUID,
    form: BoardGradeCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardGradeService = Depends(),
) -> BoardGradeResponse:
    result = await service.create(user.id, board_id, form)
    response.headers["Location"] = f"/api/v1/boards/{board_id}/grades/{result.grade.id}"
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.patch(
    "/{board_id}/grades/order",
    response_model=BoardGradesResponse,
    responses=current_user_error_responses(
        board_error_responses(
            *GRADE_WRITE_CODES,
            BoardErrorCode.INVALID_GRADE_ORDER,
        )
    ),
)
async def reorder_grades(
    board_id: UUID,
    form: BoardGradeOrderForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardGradeService = Depends(),
) -> BoardGradesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.reorder(user.id, board_id, form)


@router.patch(
    "/{board_id}/grades/{grade_id}",
    response_model=BoardGradeResponse,
    responses=current_user_error_responses(
        board_error_responses(
            *GRADE_WRITE_CODES,
            BoardErrorCode.GRADE_NOT_FOUND,
            BoardErrorCode.GRADE_NAME_TAKEN,
        )
    ),
)
async def change_grade(
    board_id: UUID,
    grade_id: UUID,
    form: BoardGradePatchForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardGradeService = Depends(),
) -> BoardGradeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change(user.id, board_id, grade_id, form)


@router.delete(
    "/{board_id}/grades/{grade_id}",
    response_model=BoardGradesResponse,
    responses=current_user_error_responses(
        board_error_responses(
            *GRADE_WRITE_CODES,
            BoardErrorCode.GRADE_NOT_FOUND,
            BoardErrorCode.INVALID_GRADE,
            BoardErrorCode.LAST_GRADE,
        )
    ),
)
async def delete_grade(
    board_id: UUID,
    grade_id: UUID,
    form: BoardGradeDeleteForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardGradeService = Depends(),
) -> BoardGradesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.delete(user.id, board_id, grade_id, form)


MEMBER_READ_CODES = (
    BoardErrorCode.NOT_FOUND,
    BoardErrorCode.FORBIDDEN,
    BoardErrorCode.INVALID_CURSOR,
    BoardErrorCode.UNAVAILABLE,
)
MEMBER_READ_ERRORS = current_user_error_responses(board_error_responses(*MEMBER_READ_CODES))
MEMBER_PATCH_ERRORS = current_user_error_responses(
    board_error_responses(
        BoardErrorCode.NOT_FOUND,
        BoardErrorCode.FORBIDDEN,
        BoardErrorCode.MEMBER_NOT_FOUND,
        BoardErrorCode.INVALID_GRADE,
        BoardErrorCode.INVALID_MEMBER_CHANGE,
        BoardErrorCode.CONFLICT,
        BoardErrorCode.UNAVAILABLE,
    )
)
MEMBER_AUDIT_ERRORS = current_user_error_responses(
    board_error_responses(*MEMBER_READ_CODES, BoardErrorCode.INVALID_AUDIT_WINDOW)
)


@router.get(
    "/{board_id}/members", response_model=BoardMemberListResponse, responses=MEMBER_READ_ERRORS
)
async def members(
    board_id: UUID,
    response: Response,
    query: BoardMembersQuery = Depends(),
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMembershipService = Depends(),
) -> BoardMemberListResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.members(user.id, board_id, query)


@router.patch(
    "/{board_id}/members/{user_id}",
    response_model=BoardMemberUpdateResponse,
    responses=MEMBER_PATCH_ERRORS,
)
async def update_member(
    board_id: UUID,
    user_id: int,
    form: BoardMemberPatchForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMembershipService = Depends(),
) -> BoardMemberUpdateResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change_member(user.id, board_id, user_id, form)


@router.get(
    "/{board_id}/member-audit", response_model=BoardAuditPageResponse, responses=MEMBER_AUDIT_ERRORS
)
async def member_audit(
    board_id: UUID,
    response: Response,
    query: BoardAuditQuery = Depends(),
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMembershipService = Depends(),
) -> BoardAuditPageResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.member_audit(user.id, board_id, query)
