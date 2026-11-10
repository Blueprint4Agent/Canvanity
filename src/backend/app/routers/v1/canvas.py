from collections.abc import Awaitable, Callable
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.routing import APIRoute
from starlette.types import Message

from app.core.error.asset_exception import AssetErrorCode, asset_error_responses
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException, canvas_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user, get_current_token_user
from app.models.canvas import (
    CanvasCreateForm,
    CanvasDocumentResponse,
    CanvasDocumentSaveForm,
    CanvasDocumentSaveResponse,
    CanvasDocumentValidationErrorResponse,
    CanvasLikeResponse,
    CanvasMetadataValidationErrorResponse,
    CanvasPatchForm,
    CanvasPublicationDocumentResponse,
    CanvasPublicationMutationResponse,
    CanvasPublicationResponse,
    CanvasPublishForm,
    CanvasResponse,
    CanvasRevisionForm,
    CanvasUnpublishForm,
)
from app.models.canvas_comment import (
    CommentCreateForm,
    CommentPage,
    CommentPatchForm,
    CommentQuery,
    CommentResponse,
    CommentRevisionForm,
)
from app.models.canvas_feed import CanvasFeedFilters, CanvasFeedQuery, CanvasFeedResponse
from app.models.canvas_list import CanvasListQuery, CanvasListResponse
from app.models.user import UserResponse
from app.services.canvas import CanvasService
from app.services.canvas_comment import CanvasCommentService
from app.services.canvas_feed import CanvasFeedService
from app.services.canvas_like import CanvasLikeService
from app.services.canvas_list import CanvasListService
from app.utils.canvas_limits import MAX_CANVAS_DOCUMENT_REQUEST_BYTES


class CanvasDocumentRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        handler = super().get_route_handler()

        async def bounded_document(request: Request) -> Response:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_CANVAS_DOCUMENT_REQUEST_BYTES:
                    raise CanvasException(CanvasErrorCode.DOCUMENT_TOO_LARGE)
                body.extend(chunk)
            payload = bytes(body)
            del body
            replayed = False

            async def receive() -> Message:
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type": "http.request", "body": payload, "more_body": False}
                return await request.receive()

            return await handler(Request(request.scope, receive=receive))

        return bounded_document


router = APIRouter()
document_router = APIRouter(route_class=CanvasDocumentRoute)
READ_CODES = (CanvasErrorCode.NOT_FOUND, CanvasErrorCode.UNAVAILABLE)
READ_ERRORS = current_user_error_responses(canvas_error_responses(*READ_CODES))
WRITE_CODES = (*READ_CODES, CanvasErrorCode.FORBIDDEN, CanvasErrorCode.CONFLICT)
FEED_ERRORS = current_user_error_responses(
    canvas_error_responses(*READ_CODES, CanvasErrorCode.INVALID_CURSOR),
    {status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CanvasMetadataValidationErrorResponse}},
)

COMMENT_ERRORS = current_user_error_responses(
    canvas_error_responses(
        *READ_CODES,
        CanvasErrorCode.FORBIDDEN,
        CanvasErrorCode.INVALID_CURSOR,
        CanvasErrorCode.COMMENT_CONFLICT,
    ),
    {status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CanvasMetadataValidationErrorResponse}},
)


@router.get(
    "/canvases/{canvas_id}/comments",
    response_model=CommentPage,
    responses=COMMENT_ERRORS,
    openapi_extra={"security": [{}]},
)
async def list_canvas_comments(
    canvas_id: UUID,
    query: Annotated[CommentQuery, Query()],
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasCommentService = Depends(),
) -> CommentPage:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(user.id if user else None, canvas_id, query)


@router.post(
    "/canvases/{canvas_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses=COMMENT_ERRORS,
)
async def create_canvas_comment(
    canvas_id: UUID,
    form: CommentCreateForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasCommentService = Depends(),
) -> CommentResponse:
    result = await service.create(user.id, canvas_id, form)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Location"] = f"/api/v1/canvases/{canvas_id}/comments/{result.id}"
    return result


@router.get(
    "/canvases/{canvas_id}/comments/{comment_id}",
    response_model=CommentResponse,
    responses=COMMENT_ERRORS,
    openapi_extra={"security": [{}]},
)
async def get_canvas_comment(
    canvas_id: UUID,
    comment_id: UUID,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasCommentService = Depends(),
) -> CommentResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get(user.id if user else None, canvas_id, comment_id)


@router.patch(
    "/canvases/{canvas_id}/comments/{comment_id}",
    response_model=CommentResponse,
    responses=COMMENT_ERRORS,
)
async def change_canvas_comment(
    canvas_id: UUID,
    comment_id: UUID,
    form: CommentPatchForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasCommentService = Depends(),
) -> CommentResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change(user.id, canvas_id, comment_id, form)


@router.delete(
    "/canvases/{canvas_id}/comments/{comment_id}",
    response_model=CommentResponse,
    responses=COMMENT_ERRORS,
)
async def delete_canvas_comment(
    canvas_id: UUID,
    comment_id: UUID,
    form: CommentRevisionForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasCommentService = Depends(),
) -> CommentResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.change(user.id, canvas_id, comment_id, form, delete=True)


@router.get(
    "/canvases/{canvas_id}/like",
    response_model=CanvasLikeResponse,
    responses=READ_ERRORS,
    openapi_extra={"security": [{}]},
)
async def get_canvas_like(
    canvas_id: UUID,
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasLikeService = Depends(),
) -> CanvasLikeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get(user.id if user else None, canvas_id)


@router.put(
    "/canvases/{canvas_id}/like",
    response_model=CanvasLikeResponse,
    responses=current_user_error_responses(
        canvas_error_responses(*READ_CODES, CanvasErrorCode.FORBIDDEN)
    ),
)
async def like_canvas(
    canvas_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasLikeService = Depends(),
) -> CanvasLikeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.set(user.id, canvas_id, liked=True)


@router.delete(
    "/canvases/{canvas_id}/like",
    response_model=CanvasLikeResponse,
    responses=current_user_error_responses(
        canvas_error_responses(*READ_CODES, CanvasErrorCode.FORBIDDEN)
    ),
)
async def unlike_canvas(
    canvas_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasLikeService = Depends(),
) -> CanvasLikeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.set(user.id, canvas_id, liked=False)


@router.get("/me/canvases", response_model=CanvasListResponse, responses=FEED_ERRORS)
async def list_my_canvases(
    query: Annotated[CanvasListQuery, Query()],
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasListService = Depends(),
) -> CanvasListResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(user.id, query)


@router.get(
    "/canvases",
    response_model=CanvasFeedResponse,
    responses=FEED_ERRORS,
    openapi_extra={"security": [{}]},
)
async def list_canvases(
    query: Annotated[CanvasFeedQuery, Query()],
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasFeedService = Depends(),
) -> CanvasFeedResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(user.id if user else None, query, scope="plaza")


@router.get(
    "/boards/{board_id}/canvases",
    response_model=CanvasFeedResponse,
    responses=FEED_ERRORS,
    openapi_extra={"security": [{}]},
)
async def list_board_canvases(
    board_id: UUID,
    query: Annotated[CanvasFeedFilters, Query()],
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasFeedService = Depends(),
) -> CanvasFeedResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(
        user.id if user else None,
        CanvasFeedQuery(**query.model_dump(), board_id=board_id),
        scope=f"board:{board_id}",
    )


@router.get(
    "/shelves/{shelf_id}/canvases",
    response_model=CanvasFeedResponse,
    responses=FEED_ERRORS,
    openapi_extra={"security": [{}]},
)
async def list_shelf_canvases(
    shelf_id: UUID,
    query: Annotated[CanvasFeedFilters, Query()],
    response: Response,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasFeedService = Depends(),
) -> CanvasFeedResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.list(
        user.id if user else None,
        CanvasFeedQuery(**query.model_dump(), shelf_id=shelf_id),
        scope=f"shelf:{shelf_id}",
    )


@router.post(
    "/boards/{board_id}/canvases",
    response_model=CanvasResponse,
    status_code=status.HTTP_201_CREATED,
    responses=current_user_error_responses(
        canvas_error_responses(
            *READ_CODES,
            CanvasErrorCode.FORBIDDEN,
            CanvasErrorCode.INVALID_SHELF,
            CanvasErrorCode.INVALID_TAGS,
        ),
        {status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CanvasMetadataValidationErrorResponse}},
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


@router.get(
    "/canvases/{canvas_id}",
    response_model=CanvasResponse | CanvasPublicationResponse,
    responses=READ_ERRORS,
    openapi_extra={"security": [{}]},
)
async def get_canvas(
    canvas_id: UUID,
    response: Response,
    view: Literal["draft", "publication"] | None = None,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasService = Depends(),
) -> CanvasResponse | CanvasPublicationResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.get(user.id if user else None, canvas_id, view=view)


@router.get(
    "/canvases/{canvas_id}/document",
    response_model=CanvasDocumentResponse | CanvasPublicationDocumentResponse,
    responses=READ_ERRORS,
    openapi_extra={"security": [{}]},
)
async def get_canvas_document(
    canvas_id: UUID,
    response: Response,
    view: Literal["draft", "publication"] | None = None,
    user: UserResponse | None = Depends(get_current_token_user),
    service: CanvasService = Depends(),
) -> CanvasDocumentResponse | CanvasPublicationDocumentResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.document(user.id if user else None, canvas_id, view=view)


@router.post(
    "/canvases/{canvas_id}/publish",
    response_model=CanvasPublicationMutationResponse,
    responses=current_user_error_responses(
        canvas_error_responses(
            *WRITE_CODES,
            CanvasErrorCode.DOCUMENT_CONFLICT,
            CanvasErrorCode.PUBLICATION_CONFLICT,
            CanvasErrorCode.DOCUMENT_INVALID,
            CanvasErrorCode.INVALID_STATE,
        ),
        asset_error_responses(AssetErrorCode.INVALID_REFERENCE),
        {status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CanvasDocumentValidationErrorResponse}},
    ),
)
async def publish_canvas(
    canvas_id: UUID,
    form: CanvasPublishForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasPublicationMutationResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.publish(user.id, canvas_id, form)


@router.post(
    "/canvases/{canvas_id}/unpublish",
    response_model=CanvasPublicationMutationResponse,
    responses=current_user_error_responses(
        canvas_error_responses(
            *READ_CODES,
            CanvasErrorCode.FORBIDDEN,
            CanvasErrorCode.PUBLICATION_CONFLICT,
            CanvasErrorCode.INVALID_STATE,
        )
    ),
)
async def unpublish_canvas(
    canvas_id: UUID,
    form: CanvasUnpublishForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasPublicationMutationResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.unpublish(user.id, canvas_id, form)


@document_router.put(
    "/canvases/{canvas_id}/document",
    response_model=CanvasDocumentSaveResponse,
    responses=current_user_error_responses(
        canvas_error_responses(
            *READ_CODES,
            CanvasErrorCode.FORBIDDEN,
            CanvasErrorCode.INVALID_STATE,
            CanvasErrorCode.DOCUMENT_CONFLICT,
            CanvasErrorCode.DOCUMENT_TOO_LARGE,
        ),
        asset_error_responses(AssetErrorCode.INVALID_REFERENCE),
        {
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "model": CanvasDocumentValidationErrorResponse,
                "description": "Request validation failed.",
            }
        },
    ),
)
async def save_canvas_document(
    canvas_id: UUID,
    form: CanvasDocumentSaveForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: CanvasService = Depends(),
) -> CanvasDocumentSaveResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.save_document(user.id, canvas_id, form)


@router.patch(
    "/canvases/{canvas_id}",
    response_model=CanvasResponse,
    responses=current_user_error_responses(
        canvas_error_responses(
            *WRITE_CODES,
            CanvasErrorCode.INVALID_SHELF,
            CanvasErrorCode.INVALID_STATE,
            CanvasErrorCode.INVALID_TAGS,
        ),
        {status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CanvasMetadataValidationErrorResponse}},
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
    responses=current_user_error_responses(
        canvas_error_responses(*WRITE_CODES, CanvasErrorCode.PUBLICATION_CONFLICT)
    ),
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


router.include_router(document_router)
