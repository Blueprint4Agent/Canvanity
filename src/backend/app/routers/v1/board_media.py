"""Bounded multipart transport and guarded versioned Board image responses."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status
from fastapi.routing import APIRoute
from starlette.types import Message

from app.core.error.asset_exception import AssetErrorCode, AssetException, asset_error_responses
from app.core.error.board_exception import BoardErrorCode, board_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user, get_current_token_user
from app.models.board_media import (
    BoardMediaChangeForm,
    BoardMediaMultipartError,
    BoardMediaSlot,
    BoardMediaUpdateResponse,
)
from app.models.user import UserResponse
from app.services.asset import MAX_IMAGE_BYTES
from app.services.board_media import BoardMediaService
from app.utils.form_fields import AuditReason, MultipartInt32

MAX_BOARD_MEDIA_REQUEST_BYTES = MAX_IMAGE_BYTES + 64 * 1024


class BoardMediaRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        handler = super().get_route_handler()

        async def bounded_upload(request: Request) -> Response:
            if request.method != "PUT":
                return await handler(request)
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_BOARD_MEDIA_REQUEST_BYTES:
                    raise AssetException(AssetErrorCode.TOO_LARGE)
                body.extend(chunk)
            replayed = False

            async def receive() -> Message:
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await request.receive()

            bounded = Request(request.scope, receive=receive)
            form = await bounded.form(max_files=1, max_fields=2, max_part_size=2048)
            try:
                return await handler(bounded)
            finally:
                await form.close()

        return bounded_upload


router = APIRouter(route_class=BoardMediaRoute)
WRITE_ERRORS = current_user_error_responses(
    board_error_responses(
        BoardErrorCode.NOT_FOUND,
        BoardErrorCode.FORBIDDEN,
        BoardErrorCode.CONFLICT,
        BoardErrorCode.REVISION_EXHAUSTED,
        BoardErrorCode.MEDIA_LIMIT_REACHED,
        BoardErrorCode.MEDIA_CONFLICT,
        BoardErrorCode.UNAVAILABLE,
    ),
    asset_error_responses(
        AssetErrorCode.INVALID_IMAGE, AssetErrorCode.TOO_LARGE, AssetErrorCode.UNAVAILABLE
    ),
)


@router.put(
    "/boards/{board_id}/media/{slot}",
    response_model=BoardMediaUpdateResponse,
    responses={
        **WRITE_ERRORS,
        status.HTTP_400_BAD_REQUEST: {
            "model": BoardMediaMultipartError,
            "description": "multipart 파일/필드 개수 또는 텍스트 part 한도 초과.",
        },
    },
)
async def upload_board_media(
    board_id: UUID,
    slot: BoardMediaSlot,
    response: Response,
    expected_revision: Annotated[MultipartInt32, Form()],
    reason: Annotated[AuditReason, Form()],
    file: UploadFile = File(...),
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMediaService = Depends(),
) -> BoardMediaUpdateResponse:
    async def chunks():
        while chunk := await file.read(64 * 1024):
            yield chunk

    try:
        result = await service.upload(
            user.id,
            board_id,
            slot,
            BoardMediaChangeForm(expected_revision=expected_revision, reason=reason),
            chunks(),
        )
    finally:
        await file.close()
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Location"] = result.media.url
    return result


@router.delete(
    "/boards/{board_id}/media/{slot}",
    response_model=BoardMediaUpdateResponse,
    responses=WRITE_ERRORS,
)
async def remove_board_media(
    board_id: UUID,
    slot: BoardMediaSlot,
    form: BoardMediaChangeForm,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: BoardMediaService = Depends(),
) -> BoardMediaUpdateResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await service.remove(user.id, board_id, slot, form)


@router.get(
    "/boards/{board_id}/media/{slot}/{asset_id}",
    response_class=Response,
    openapi_extra={"security": [{}]},
    responses={
        status.HTTP_200_OK: {
            "description": "현재 Board 이미지.",
            "content": {"image/webp": {"schema": {"type": "string", "format": "binary"}}},
        },
        **current_user_error_responses(
            board_error_responses(
                BoardErrorCode.NOT_FOUND, BoardErrorCode.MEDIA_NOT_FOUND, BoardErrorCode.UNAVAILABLE
            ),
            asset_error_responses(AssetErrorCode.UNAVAILABLE),
        ),
    },
)
async def read_board_media(
    board_id: UUID,
    slot: BoardMediaSlot,
    asset_id: UUID,
    user: UserResponse | None = Depends(get_current_token_user),
    service: BoardMediaService = Depends(),
) -> Response:
    data = await service.read(user.id if user else None, board_id, slot, asset_id)
    return Response(
        data,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{asset_id}.webp"',
        },
    )
