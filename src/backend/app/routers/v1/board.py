from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.error.board_exception import BoardErrorCode, board_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user, get_current_token_user
from app.models.board import (
    BoardCreateForm,
    BoardDeleteForm,
    BoardHomeResponse,
    BoardPageResponse,
    BoardSummary,
    MembershipSummary,
)
from app.models.user import UserResponse
from app.services.board import BoardService
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
