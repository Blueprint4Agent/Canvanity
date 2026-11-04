"""Feed orchestration and strict scope/filter-bound cursor transport."""

import base64
import binascii
import hashlib
import json
import re
from datetime import datetime
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.canvas_feed import (
    CanvasFeedCursor,
    CanvasFeedQuery,
    CanvasFeedRepository,
    CanvasFeedResponse,
)


def unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate cursor key.")
        result[key] = value
    return result


class CanvasFeedService:
    def __init__(self, repository: CanvasFeedRepository = Depends()):
        self.repository = repository

    @staticmethod
    def _filter_hash(query: CanvasFeedQuery) -> str:
        filters = query.model_dump(mode="json", exclude={"limit", "sort", "cursor"})
        return hashlib.sha256(
            json.dumps(filters, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _before(cursor: str | None, scope: str, filter_hash: str) -> tuple[datetime, UUID] | None:
        if cursor is None:
            return None
        try:
            if len(cursor) > 2048 or not re.fullmatch(r"[A-Za-z0-9_-]+", cursor):
                raise ValueError("Invalid cursor encoding.")
            raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
            if base64.urlsafe_b64encode(raw).decode().rstrip("=") != cursor:
                raise ValueError("Non-canonical cursor encoding.")
            json.loads(raw, object_pairs_hook=unique_json_object)
            payload = CanvasFeedCursor.model_validate_json(raw)
            if payload.scope != scope or payload.filter_hash != filter_hash:
                raise ValueError("Cursor scope or filters changed.")
        except (ValueError, UnicodeError, binascii.Error, ValidationError):
            raise CanvasException(CanvasErrorCode.INVALID_CURSOR) from None
        return payload.published_at, payload.canvas_id

    async def list(
        self, user_id: int | None, query: CanvasFeedQuery, *, scope: str
    ) -> CanvasFeedResponse:
        filter_hash = self._filter_hash(query)
        before = self._before(query.cursor, scope, filter_hash)
        rows = await self.repository.read(user_id, query, before)
        if not rows.account_active:
            raise AuthException(AuthErrorCode.USER_NOT_FOUND)
        if not rows.scope_readable:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        items = rows.items[: query.limit]
        cursor = None
        if len(rows.items) > query.limit:
            last = items[-1]
            payload = {
                "v": 1,
                "domain": "canvas-publication-feed",
                "scope": scope,
                "sort": query.sort,
                "filter_hash": filter_hash,
                "published_at": last.published_at.isoformat(),
                "canvas_id": str(last.canvas.id),
            }
            cursor = (
                base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
                .decode()
                .rstrip("=")
            )
        return CanvasFeedResponse(items=items, next_cursor=cursor)
