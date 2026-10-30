from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class BoardErrorCode(Enum):
    NOT_FOUND = ServiceErrorCode("BOARD_NOT_FOUND", "Board not found.", status.HTTP_404_NOT_FOUND)
    FORBIDDEN = ServiceErrorCode(
        "BOARD_FORBIDDEN",
        "You do not have permission to perform this board operation.",
        status.HTTP_403_FORBIDDEN,
    )
    SLUG_TAKEN = ServiceErrorCode(
        "BOARD_SLUG_TAKEN", "Board slug already exists.", status.HTTP_409_CONFLICT
    )
    LIMIT_REACHED = ServiceErrorCode(
        "BOARD_LIMIT_REACHED",
        "The board creation limit has been reached.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_INTEREST = ServiceErrorCode(
        "BOARD_INVALID_INTEREST",
        "Select active official interests.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_SETTINGS = ServiceErrorCode(
        "BOARD_INVALID_SETTINGS",
        "Private boards require invite membership; include it when making a board private.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_CURSOR = ServiceErrorCode(
        "BOARD_INVALID_CURSOR",
        "Invalid board cursor. Reload the list.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    CONFLICT = ServiceErrorCode(
        "BOARD_REVISION_CONFLICT",
        "Board revision conflict. Reload the latest board information.",
        status.HTTP_409_CONFLICT,
    )
    DELETE_CONFIRMATION = ServiceErrorCode(
        "BOARD_DELETE_CONFIRMATION",
        "Enter the exact board slug to confirm deletion.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    NOT_EMPTY = ServiceErrorCode(
        "BOARD_NOT_EMPTY",
        "Remove other members and content before deleting the board.",
        status.HTTP_409_CONFLICT,
    )

    OWNER_CANNOT_LEAVE = ServiceErrorCode(
        "BOARD_OWNER_CANNOT_LEAVE",
        "Transfer ownership or delete the board before leaving.",
        status.HTTP_409_CONFLICT,
    )

    MEMBER_NOT_FOUND = ServiceErrorCode(
        "BOARD_MEMBER_NOT_FOUND", "Board member not found.", status.HTTP_404_NOT_FOUND
    )
    INVITEE_NOT_FOUND = ServiceErrorCode(
        "BOARD_INVITEE_NOT_FOUND", "Active invitee account not found.", status.HTTP_404_NOT_FOUND
    )
    INVITATION_CONFLICT = ServiceErrorCode(
        "BOARD_INVITATION_CONFLICT",
        "Use member management to update an existing inactive membership.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_GRADE = ServiceErrorCode(
        "BOARD_INVALID_GRADE",
        "Select a member grade from the same board.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    GRADE_NOT_FOUND = ServiceErrorCode(
        "BOARD_GRADE_NOT_FOUND", "Board member grade not found.", status.HTTP_404_NOT_FOUND
    )
    GRADE_NAME_TAKEN = ServiceErrorCode(
        "BOARD_GRADE_NAME_TAKEN", "Member grade name already exists.", status.HTTP_409_CONFLICT
    )
    GRADE_RANK_TAKEN = ServiceErrorCode(
        "BOARD_GRADE_RANK_TAKEN", "Member grade rank already exists.", status.HTTP_409_CONFLICT
    )
    GRADE_LIMIT_REACHED = ServiceErrorCode(
        "BOARD_GRADE_LIMIT_REACHED",
        "The member grade limit has been reached.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_GRADE_ORDER = ServiceErrorCode(
        "BOARD_INVALID_GRADE_ORDER",
        "Provide every grade in this board exactly once.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    LAST_GRADE = ServiceErrorCode(
        "BOARD_LAST_GRADE", "The last member grade cannot be deleted.", status.HTTP_409_CONFLICT
    )
    INVALID_MEMBER_CHANGE = ServiceErrorCode(
        "BOARD_INVALID_MEMBER_CHANGE",
        "The final membership status must be active to assign an operational role.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_AUDIT_WINDOW = ServiceErrorCode(
        "BOARD_INVALID_AUDIT_WINDOW",
        "Provide timezone-aware start and end times within a maximum window of 180 days.",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

    UNAVAILABLE = ServiceErrorCode(
        "BOARD_UNAVAILABLE",
        "Unable to complete the board operation.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
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
