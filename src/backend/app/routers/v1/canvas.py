from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.error.canvas_exception import CanvasErrorCode, canvas_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user
from app.models.canvas import (
    CanvasCreateForm,
    CanvasDocumentResponse,
    CanvasPatchForm,
    CanvasResponse,
    CanvasRevisionForm,
)
from app.models.user import UserResponse
from app.services.canvas import CanvasService

router = APIRouter()
READ_CODES = (CanvasErrorCode.NOT_FOUND, CanvasErrorCode.UNAVAILABLE)
READ_ERRORS = current_user_error_responses(canvas_error_responses(*READ_CODES))
WRITE_CODES = (*READ_CODES, CanvasErrorCode.FORBIDDEN, CanvasErrorCode.CONFLICT)


@router.post(
    "/boards/{board_id}/canvases",
    response_model=CanvasResponse,
    status_code=status.HTTP_201_CREATED,
    responses=current_user_error_responses(
        canvas_error_responses(
            *READ_CODES, CanvasErrorCode.FORBIDDEN, CanvasErrorCode.INVALID_SHELF
        )
    ),
)
async def create_canvas(
    board_id: UUID,
    form: CanvasCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasResponse:
    result = await service.create(user.id, board_id, form)
    response.headers["Location"] = f"/api/v1/canvases/{result.canvas.id}"
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/canvases/{canvas_id}", response_model=CanvasResponse, responses=READ_ERRORS)
async def get_canvas(
    canvas_id: UUID,
    response: Response,
    view: Literal["draft"] = "draft",
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get(user.id, canvas_id)


@router.get(
    "/canvases/{canvas_id}/document", response_model=CanvasDocumentResponse, responses=READ_ERRORS
)
async def get_canvas_document(
    canvas_id: UUID,
    response: Response,
    view: Literal["draft"] = "draft",
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasDocumentResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.document(user.id, canvas_id)


@router.patch(
    "/canvases/{canvas_id}",
    response_model=CanvasResponse,
    responses=current_user_error_responses(
        canvas_error_responses(
            *WRITE_CODES, CanvasErrorCode.INVALID_SHELF, CanvasErrorCode.INVALID_STATE
        )
    ),
)
async def change_canvas(
    canvas_id: UUID,
    form: CanvasPatchForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change(user.id, canvas_id, form)


@router.delete(
    "/canvases/{canvas_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=current_user_error_responses(canvas_error_responses(*WRITE_CODES)),
)
async def trash_canvas(
    canvas_id: UUID,
    form: CanvasRevisionForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> None:
    response.headers["X-Canvas-Revision"] = str(await service.trash(user.id, canvas_id, form))
    response.headers["Cache-Control"] = "private, no-store"


@router.post(
    "/canvases/{canvas_id}/restore",
    response_model=CanvasResponse,
    responses=current_user_error_responses(
        canvas_error_responses(*WRITE_CODES, CanvasErrorCode.RESTORE_EXPIRED)
    ),
)
async def restore_canvas(
    canvas_id: UUID,
    form: CanvasRevisionForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.restore(user.id, canvas_id, form)
