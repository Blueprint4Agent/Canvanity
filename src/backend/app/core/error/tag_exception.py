from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class TagErrorCode(Enum):
    UNAVAILABLE = ServiceErrorCode(
        "TAG_UNAVAILABLE",
        "Unable to complete the tag operation.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class TagException(ServiceException):
    def __init__(self, code: TagErrorCode):
        super().__init__(code=code.code)


TagErrorDetail, TagErrorResponse = build_error_models(
    detail_model_name="TagErrorDetail",
    response_model_name="TagErrorResponse",
    error_values=[code.code.error for code in TagErrorCode],
    example_error=TagErrorCode.UNAVAILABLE.code.error,
)


def tag_error_responses(*codes: TagErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=TagErrorResponse, codes=(code.code for code in codes)
    )
