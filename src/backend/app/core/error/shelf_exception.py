from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class ShelfErrorCode(Enum):
    NOT_EMPTY = ServiceErrorCode(
        "SHELF_NOT_EMPTY",
        "Move all canvases, including drafts and trash, before deleting this shelf.",
        status.HTTP_409_CONFLICT,
    )
    NOT_FOUND = ServiceErrorCode("SHELF_NOT_FOUND", "Shelf not found.", status.HTTP_404_NOT_FOUND)
    SLUG_TAKEN = ServiceErrorCode(
        "SHELF_SLUG_TAKEN", "Shelf slug already exists in this board.", status.HTTP_409_CONFLICT
    )
    LIMIT_REACHED = ServiceErrorCode(
        "SHELF_LIMIT_REACHED", "The board shelf limit has been reached.", status.HTTP_409_CONFLICT
    )
    PROTECTED = ServiceErrorCode(
        "SHELF_PROTECTED", "The default or last shelf cannot be deleted.", status.HTTP_409_CONFLICT
    )
    INVALID_ORDER = ServiceErrorCode(
        "SHELF_INVALID_ORDER",
        "Provide every shelf in this board exactly once.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_POLICY = ServiceErrorCode(
        "SHELF_INVALID_POLICY",
        "Notice posts and comments require explicit staff-only policies.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class ShelfException(ServiceException):
    def __init__(self, code: ShelfErrorCode):
        super().__init__(code=code.code)


ShelfErrorDetail, ShelfErrorResponse = build_error_models(
    detail_model_name="ShelfErrorDetail",
    response_model_name="ShelfErrorResponse",
    error_values=[code.code.error for code in ShelfErrorCode],
    example_error=ShelfErrorCode.NOT_FOUND.code.error,
)


def shelf_error_responses(*codes: ShelfErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=ShelfErrorResponse, codes=(code.code for code in codes)
    )
