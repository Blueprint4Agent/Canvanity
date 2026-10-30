from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.error.board_exception import BoardErrorCode, board_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.core.error.shelf_exception import ShelfErrorCode, shelf_error_responses
from app.deps import get_current_session_user, get_current_token_user
from app.models.board import (
    BoardPoliciesForm,
    BoardPoliciesResponse,
    PolicyChangeForm,
    ShelfCreateForm,
    ShelfOrderForm,
    ShelfPatchForm,
    ShelfPoliciesForm,
    ShelfPoliciesResponse,
    ShelfResponse,
    ShelvesResponse,
)
from app.models.user import UserResponse
from app.services.shelf import ShelfService

router = APIRouter()


def _responses(*codes: ShelfErrorCode, write: bool = False) -> dict:
    board_codes = [BoardErrorCode.NOT_FOUND, BoardErrorCode.FORBIDDEN, BoardErrorCode.UNAVAILABLE]
    if write:
        board_codes.extend([BoardErrorCode.CONFLICT, BoardErrorCode.INVALID_GRADE])
    return current_user_error_responses(
        board_error_responses(*board_codes), shelf_error_responses(ShelfErrorCode.NOT_FOUND, *codes)
    )


@router.get(
    "/boards/{board_id}/shelves",
    response_model=ShelvesResponse,
    openapi_extra={"security": [{}]},
    responses=_responses(),
)
async def list_shelves(
    board_id: UUID,
    response: Response,
    manage: bool = False,
    user: UserResponse | None = Depends(get_current_token_user),
    service: ShelfService = Depends(),
) -> ShelvesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(user.id if user else None, board_id, manage=manage)


@router.get(
    "/shelves/{shelf_id}",
    response_model=ShelfResponse,
    openapi_extra={"security": [{}]},
    responses=_responses(),
)
async def get_shelf(
    shelf_id: UUID,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: ShelfService = Depends(),
) -> ShelfResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get(user.id if user else None, shelf_id)


@router.post(
    "/boards/{board_id}/shelves",
    response_model=ShelfResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_responses(ShelfErrorCode.SLUG_TAKEN, ShelfErrorCode.LIMIT_REACHED, write=True),
)
async def create_shelf(
    board_id: UUID,
    form: ShelfCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> ShelfResponse:
    result = await service.create(user.id, board_id, form)
    response.headers["Location"] = f"/api/v1/shelves/{result.shelf.id}"
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.patch(
    "/shelves/{shelf_id}",
    response_model=ShelfResponse,
    responses=_responses(ShelfErrorCode.SLUG_TAKEN, write=True),
)
async def change_shelf(
    shelf_id: UUID,
    form: ShelfPatchForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> ShelfResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change(user.id, shelf_id, form)


@router.delete(
    "/shelves/{shelf_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_responses(ShelfErrorCode.PROTECTED, ShelfErrorCode.NOT_EMPTY, write=True),
)
async def delete_shelf(
    shelf_id: UUID,
    form: PolicyChangeForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> None:
    revision = await service.delete(user.id, shelf_id, form)
    response.headers["X-Board-Revision"] = str(revision)
    response.headers["Cache-Control"] = "private, no-store"


@router.patch(
    "/boards/{board_id}/shelves/order",
    response_model=ShelvesResponse,
    responses=_responses(ShelfErrorCode.INVALID_ORDER, write=True),
)
async def reorder_shelves(
    board_id: UUID,
    form: ShelfOrderForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> ShelvesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.reorder(user.id, board_id, form)


@router.get(
    "/boards/{board_id}/policies", response_model=BoardPoliciesResponse, responses=_responses()
)
async def board_policies(
    board_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> BoardPoliciesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.board_policies(user.id, board_id)


@router.put(
    "/boards/{board_id}/policies",
    response_model=BoardPoliciesResponse,
    responses=_responses(write=True),
)
async def set_board_policies(
    board_id: UUID,
    form: BoardPoliciesForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> BoardPoliciesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.set_board_policies(user.id, board_id, form)


@router.get(
    "/shelves/{shelf_id}/policies", response_model=ShelfPoliciesResponse, responses=_responses()
)
async def shelf_policies(
    shelf_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> ShelfPoliciesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.shelf_policies(user.id, shelf_id)


@router.put(
    "/shelves/{shelf_id}/policies",
    response_model=ShelfPoliciesResponse,
    responses=_responses(ShelfErrorCode.INVALID_POLICY, write=True),
)
async def set_shelf_policies(
    shelf_id: UUID,
    form: ShelfPoliciesForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: ShelfService = Depends(),
) -> ShelfPoliciesResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.set_shelf_policies(user.id, shelf_id, form)
