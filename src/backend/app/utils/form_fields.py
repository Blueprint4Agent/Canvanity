"""Pure text-to-scalar transport validation, without workflow or persistence policy."""

import re
from typing import Annotated

from pydantic import BeforeValidator, Field, StringConstraints

MAX_INT32 = 2**31 - 1
AuditReason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


def ascii_decimal_int32(value: object) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{1,10}", value) is None:
        raise ValueError("Use an unsigned ASCII decimal integer.")
    return int(value)


MultipartInt32 = Annotated[
    int, BeforeValidator(ascii_decimal_int32), Field(ge=0, le=MAX_INT32, strict=True)
]
