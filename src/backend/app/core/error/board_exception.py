from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class BoardErrorCode(Enum):
    NOT_FOUND = ServiceErrorCode(
        "BOARD_NOT_FOUND", "보드를 찾을 수 없습니다.", status.HTTP_404_NOT_FOUND
    )
    FORBIDDEN = ServiceErrorCode(
        "BOARD_FORBIDDEN", "보드 작업 권한이 없습니다.", status.HTTP_403_FORBIDDEN
    )
    SLUG_TAKEN = ServiceErrorCode(
        "BOARD_SLUG_TAKEN", "이미 사용 중인 보드 주소입니다.", status.HTTP_409_CONFLICT
    )
    LIMIT_REACHED = ServiceErrorCode(
        "BOARD_LIMIT_REACHED", "보드는 최대 20개까지 개설할 수 있습니다.", status.HTTP_409_CONFLICT
    )
    INVALID_INTEREST = ServiceErrorCode(
        "BOARD_INVALID_INTEREST",
        "활성 공식 관심사를 선택해 주세요.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_CURSOR = ServiceErrorCode(
        "BOARD_INVALID_CURSOR", "목록을 다시 불러와 주세요.", status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    CONFLICT = ServiceErrorCode(
        "BOARD_REVISION_CONFLICT", "최신 보드 정보를 다시 불러와 주세요.", status.HTTP_409_CONFLICT
    )
    DELETE_CONFIRMATION = ServiceErrorCode(
        "BOARD_DELETE_CONFIRMATION",
        "보드 주소를 정확히 입력해 주세요.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    NOT_EMPTY = ServiceErrorCode(
        "BOARD_NOT_EMPTY",
        "다른 회원이나 게시글이 있는 보드는 먼저 정리해 주세요.",
        status.HTTP_409_CONFLICT,
    )

    UNAVAILABLE = ServiceErrorCode(
        "BOARD_UNAVAILABLE", "보드 작업을 완료하지 못했습니다.", status.HTTP_503_SERVICE_UNAVAILABLE
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class BoardException(ServiceException):
    def __init__(self, code: BoardErrorCode, details: dict | None = None):
        super().__init__(code=code.code, details=details)


BoardErrorDetail, BoardErrorResponse = build_error_models(
    detail_model_name="BoardErrorDetail",
    response_model_name="BoardErrorResponse",
    error_values=[code.code.error for code in BoardErrorCode],
    example_error=BoardErrorCode.NOT_FOUND.code.error,
)


def board_error_responses(*codes: BoardErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=BoardErrorResponse, codes=(code.code for code in codes)
    )
