from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class CanvasErrorCode(Enum):
    NOT_FOUND = ServiceErrorCode("CANVAS_NOT_FOUND", "Canvas not found.", status.HTTP_404_NOT_FOUND)
    FORBIDDEN = ServiceErrorCode(
        "CANVAS_FORBIDDEN",
        "You do not have permission to perform this canvas operation.",
        status.HTTP_403_FORBIDDEN,
    )
    INVALID_SHELF = ServiceErrorCode(
        "CANVAS_INVALID_SHELF",
        "Select a manual shelf in the same board.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    CONFLICT = ServiceErrorCode(
        "CANVAS_REVISION_CONFLICT",
        "Canvas metadata revision conflict. Reload the latest canvas.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_STATE = ServiceErrorCode(
        "CANVAS_INVALID_STATE", "Restore the canvas before editing it.", status.HTTP_409_CONFLICT
    )
    RESTORE_EXPIRED = ServiceErrorCode(
        "CANVAS_RESTORE_EXPIRED",
        "The canvas restoration period has expired.",
        status.HTTP_409_CONFLICT,
    )
    UNAVAILABLE = ServiceErrorCode(
        "CANVAS_UNAVAILABLE",
        "Unable to complete the canvas operation.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class CanvasException(ServiceException):
    def __init__(self, code: CanvasErrorCode, details: dict | None = None):
        super().__init__(code=code.code, details=details)


CanvasErrorDetail, CanvasErrorResponse = build_error_models(
    detail_model_name="CanvasErrorDetail",
    response_model_name="CanvasErrorResponse",
    error_values=[code.code.error for code in CanvasErrorCode],
    example_error=CanvasErrorCode.NOT_FOUND.code.error,
)


def canvas_error_responses(*codes: CanvasErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=CanvasErrorResponse, codes=(code.code for code in codes)
    )
