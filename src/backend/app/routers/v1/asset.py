from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from app.core.error.asset_exception import AssetErrorCode, asset_error_responses
from app.core.error.canvas_exception import CanvasErrorCode, canvas_error_responses
from app.core.error.response_contracts import current_user_error_responses
from app.deps import get_current_session_user
from app.models.asset import AssetResponse
from app.models.user import UserResponse
from app.services.asset import AssetService

router = APIRouter()
COMMON = (
    CanvasErrorCode.NOT_FOUND,
    CanvasErrorCode.FORBIDDEN,
    CanvasErrorCode.INVALID_STATE,
    CanvasErrorCode.UNAVAILABLE,
)


@router.post(
    "/canvases/{canvas_id}/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    responses=current_user_error_responses(
        canvas_error_responses(*COMMON),
        asset_error_responses(
            AssetErrorCode.INVALID_IMAGE,
            AssetErrorCode.TOO_LARGE,
            AssetErrorCode.CONFLICT,
            AssetErrorCode.UNAVAILABLE,
            AssetErrorCode.LIMIT_REACHED,
        ),
    ),
)
async def upload_asset(
    canvas_id: UUID,
    response: Response,
    file: UploadFile = File(...),
    user: UserResponse = Depends(get_current_session_user),
    service: AssetService = Depends(),
) -> AssetResponse:
    async def chunks():
        while chunk := await file.read(64 * 1024):
            yield chunk

    try:
        asset = await service.upload(user.id, canvas_id, chunks())
    finally:
        await file.close()
    response.headers["Location"] = asset.url
    response.headers["Cache-Control"] = "private, no-store"
    return asset


@router.get(
    "/canvases/{canvas_id}/assets/{asset_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Private normalized image.",
            "content": {"image/webp": {"schema": {"type": "string", "format": "binary"}}},
        },
        **current_user_error_responses(
            canvas_error_responses(*COMMON),
            asset_error_responses(AssetErrorCode.NOT_FOUND, AssetErrorCode.UNAVAILABLE),
        ),
    },
    response_class=Response,
)
async def read_asset(
    canvas_id: UUID,
    asset_id: UUID,
    user: UserResponse = Depends(get_current_session_user),
    service: AssetService = Depends(),
) -> Response:
    data = await service.read(user.id, canvas_id, asset_id)
    return Response(
        data,
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{asset_id}.webp"',
        },
    )


@router.delete(
    "/canvases/{canvas_id}/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=current_user_error_responses(
        canvas_error_responses(*COMMON),
        asset_error_responses(
            AssetErrorCode.NOT_FOUND, AssetErrorCode.REFERENCED, AssetErrorCode.UNAVAILABLE
        ),
    ),
)
async def delete_asset(
    canvas_id: UUID,
    asset_id: UUID,
    response: Response,
    user: UserResponse = Depends(get_current_session_user),
    service: AssetService = Depends(),
) -> None:
    await service.delete(user.id, canvas_id, asset_id)
    response.headers["Cache-Control"] = "private, no-store"
