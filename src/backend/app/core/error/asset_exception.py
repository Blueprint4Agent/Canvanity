from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class AssetErrorCode(Enum):
    LIMIT_REACHED = ServiceErrorCode(
        "ASSET_LIMIT_REACHED", "The canvas asset limit has been reached.", status.HTTP_409_CONFLICT
    )
    NOT_FOUND = ServiceErrorCode("ASSET_NOT_FOUND", "Asset not found.", status.HTTP_404_NOT_FOUND)
    INVALID_IMAGE = ServiceErrorCode(
        "ASSET_INVALID_IMAGE",
        "Upload a supported image within the pixel and frame limits.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    TOO_LARGE = ServiceErrorCode(
        "ASSET_TOO_LARGE",
        "Image upload or normalized output exceeds 8 MiB.",
        status.HTTP_413_CONTENT_TOO_LARGE,
    )
    CONFLICT = ServiceErrorCode(
        "ASSET_CONFLICT",
        "The upload is no longer pending. Upload the image again.",
        status.HTTP_409_CONFLICT,
    )
    REFERENCED = ServiceErrorCode(
        "ASSET_REFERENCED",
        "The asset is referenced by a draft or publication.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_REFERENCE = ServiceErrorCode(
        "ASSET_INVALID_REFERENCE",
        "Use ready assets belonging to this canvas.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    UNAVAILABLE = ServiceErrorCode(
        "ASSET_UNAVAILABLE",
        "Unable to complete the asset operation.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class AssetException(ServiceException):
    def __init__(self, code: AssetErrorCode):
        super().__init__(code=code.code)


AssetErrorDetail, AssetErrorResponse = build_error_models(
    detail_model_name="AssetErrorDetail",
    response_model_name="AssetErrorResponse",
    error_values=[c.code.error for c in AssetErrorCode],
    example_error=AssetErrorCode.NOT_FOUND.code.error,
)


def asset_error_responses(*codes: AssetErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=AssetErrorResponse, codes=(c.code for c in codes)
    )
