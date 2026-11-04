"""Current owner list policy, shared draft capabilities and strict bound cursors."""

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
from app.models.canvas import CanvasMetadata, utc_now
from app.models.canvas_list import (
    CanvasListCursor,
    CanvasListItem,
    CanvasListQuery,
    CanvasListRepository,
    CanvasListResponse,
)
from app.services.canvas_access import CanvasAccessService
from app.services.canvas_feed import unique_json_object


class CanvasListService:
    def __init__(
        self,
        access: CanvasAccessService = Depends(),
        repository: CanvasListRepository = Depends(),
    ):
        self.access = access
        self.repository = repository

    @staticmethod
    def _filter_hash(query: CanvasListQuery) -> str:
        filters = query.model_dump(mode="json", exclude={"limit", "sort", "cursor"})
        return hashlib.sha256(
            json.dumps(filters, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _before(cursor: str | None, user_id: int, filter_hash: str) -> tuple[datetime, UUID] | None:
        if cursor is None:
            return None
        try:
            if len(cursor) > 2048 or not re.fullmatch(r"[A-Za-z0-9_-]+", cursor):
                raise ValueError("Invalid cursor encoding.")
            raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
            if base64.urlsafe_b64encode(raw).decode().rstrip("=") != cursor:
                raise ValueError("Non-canonical cursor encoding.")
            json.loads(raw, object_pairs_hook=unique_json_object)
            payload = CanvasListCursor.model_validate_json(raw)
            if payload.user_id != user_id or payload.filter_hash != filter_hash:
                raise ValueError("Cursor user or filters changed.")
        except (ValueError, UnicodeError, binascii.Error, ValidationError):
            raise CanvasException(CanvasErrorCode.INVALID_CURSOR) from None
        return payload.last_modified_at, payload.canvas_id

    async def list(self, user_id: int, query: CanvasListQuery) -> CanvasListResponse:
        filter_hash = self._filter_hash(query)
        before = self._before(query.cursor, user_id, filter_hash)
        # This is the single expiry/capability evaluation time, not a historical DB cutoff.
        as_of = utc_now()
        data = await self.repository.read(user_id, query, before)
        if not data.account_active:
            raise AuthException(AuthErrorCode.USER_NOT_FOUND)
        if not data.scope_readable:
            raise CanvasException(CanvasErrorCode.NOT_FOUND)
        if data.scope is not None:
            scope = data.scope
            readable = self.access.permissions.shelf_capabilities(
                scope.board,
                scope.member,
                scope.shelf_id,
                data.grades,
                data.policies.get(scope.board.id, {}),
                data.overrides,
            )["read_canvas"]
            if not readable and not scope.has_own:
                raise CanvasException(CanvasErrorCode.NOT_FOUND)
        items = []
        for row in data.rows[: query.limit]:
            canvas, board = row.canvas, row.board
            can_write = self.access.permissions.shelf_capabilities(
                board,
                row.member,
                canvas.shelf_id,
                data.grades,
                data.policies.get(board.id, {}),
                data.overrides,
            )["create_canvas"]
            expires = self.access.trash_expires_at(canvas)
            items.append(
                CanvasListItem(
                    canvas=CanvasMetadata.model_validate(canvas).model_copy(
                        update={"tags": data.tags.get(canvas.id, [])}
                    ),
                    document_revision=row.document_revision,
                    document_updated_at=row.document_updated_at,
                    last_modified_at=row.last_modified_at,
                    publication_revision=row.publication_revision,
                    publication=row.publication,
                    capabilities=self.access.capabilities(
                        board,
                        canvas,
                        can_write=can_write,
                        published=row.publication is not None,
                        at=as_of,
                    ),
                    trash_expires_at=expires,
                    trash_expired=expires is not None and as_of >= expires,
                )
            )
        cursor = None
        if len(data.rows) > query.limit:
            last = items[-1]
            payload = {
                "v": 1,
                "domain": "canvas-owner-list",
                "user_id": user_id,
                "sort": query.sort,
                "filter_hash": filter_hash,
                "last_modified_at": last.last_modified_at.isoformat(),
                "canvas_id": str(last.canvas.id),
            }
            cursor = (
                base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
                .decode()
                .rstrip("=")
            )
        return CanvasListResponse(items=items, as_of=as_of, next_cursor=cursor)
