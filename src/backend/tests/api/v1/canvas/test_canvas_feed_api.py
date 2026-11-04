import base64
import json
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.deps import get_current_token_user
from app.main import register_exception_handlers
from app.models.canvas_feed import CanvasFeedQuery, CanvasFeedResponse
from app.routers.v1.canvas import router
from app.services.canvas_feed import CanvasFeedService

pytestmark = pytest.mark.api_test
BOARD, SHELF, CANVAS, TAG = [str(UUID(int=n)) for n in (1, 2, 3, 4)]
PATHS = [
    "/api/v1/canvases",
    f"/api/v1/boards/{BOARD}/canvases",
    f"/api/v1/shelves/{SHELF}/canvases",
]
ITEM = {
    "canvas": {
        "id": CANVAS,
        "board_id": BOARD,
        "shelf_id": SHELF,
        "author_id": None,
        "title": "공개 제목",
        "summary": "공개 요약",
        "visibility": "public",
        "status": "published",
        "tags": [{"id": TAG, "name": "게시 태그"}],
    },
    "board": {"id": BOARD, "slug": "board", "name": "보드"},
    "shelf": {"id": SHELF, "slug": "general", "name": "자유"},
    "publication_revision": 1,
    "source_metadata_revision": 2,
    "source_document_revision": 3,
    "published_at": "2026-11-03T12:00:00Z",
    "view": "publication",
}


@pytest.fixture
def feed_api():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    service = AsyncMock(spec=CanvasFeedService)
    service.list.return_value = CanvasFeedResponse(items=[ITEM])
    app.dependency_overrides[CanvasFeedService] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize("path", PATHS)
def test_feed_routes_return_only_snapshot_headers_and_current_location(feed_api, path):
    client, service = feed_api
    response = client.get(path, params={"limit": 1, "interest_id": "ai", "tag_id": TAG})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == {"items": [ITEM], "next_cursor": None}
    user_id, query = service.list.await_args.args
    assert user_id is None and query.limit == 1 and query.sort == "latest"
    assert query.interest_id == "ai" and query.tag_id == UUID(TAG)
    assert query.board_id == (UUID(BOARD) if "/boards/" in path else None)
    assert query.shelf_id == (UUID(SHELF) if "/shelves/" in path else None)
    operation = client.app.openapi()["paths"][
        path.replace(BOARD, "{board_id}").replace(SHELF, "{shelf_id}")
    ]["get"]
    assert {} in operation["security"] and {"OAuth2PasswordBearer": []} in operation["security"]
    assert {"200", "401", "404", "422", "503"} <= operation["responses"].keys()
    error = operation["responses"]["422"]["content"]["application/json"]["schema"]
    assert {x["$ref"] for x in error["anyOf"]} == {
        "#/components/schemas/CanvasErrorResponse",
        "#/components/schemas/CanvasMetadataValidationErrorResponse",
    }


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(
    "params",
    [
        {"limit": "true"},
        {"limit": 0},
        {"limit": 101},
        {"limit": 1.5},
        {"sort": "popular"},
        {"interest_id": "AI"},
        {"interest_id": "a"},
        {"tag_id": "false"},
        {"cursor": ""},
        {"cursor": "x" * 2049},
        {"q": "secret"},
    ],
)
def test_feed_query_validation_precedes_service(feed_api, path, params):
    client, service = feed_api
    assert client.get(path, params=params).status_code == 422
    service.list.assert_not_awaited()


@pytest.mark.parametrize("path", PATHS[1:])
def test_scoped_routes_reject_location_query_overrides(feed_api, path):
    client, service = feed_api
    assert client.get(path, params={"board_id": BOARD, "shelf_id": SHELF}).status_code == 422
    service.list.assert_not_awaited()


@pytest.mark.parametrize("path", PATHS)
def test_feed_optional_auth_preserves_bearer_identity_and_api_key_is_anonymous(
    feed_api, sample_user, path
):
    client, service = feed_api
    assert client.get(path, headers={"X-API-Key": "ignored-for-public-read"}).status_code == 200
    assert service.list.await_args.args[0] is None
    service.list.reset_mock()
    denied = client.get(path, headers={"Authorization": "Bearer invalid-token"})
    assert denied.status_code == 401 and denied.json()["detail"]["error"] == "INVALID_TOKEN"
    service.list.assert_not_awaited()
    client.app.dependency_overrides[get_current_token_user] = lambda: sample_user
    assert client.get(path).status_code == 200
    assert service.list.await_args.args[0] == sample_user.id


@pytest.mark.parametrize(
    "error,status",
    [
        (CanvasException(CanvasErrorCode.NOT_FOUND), 404),
        (CanvasException(CanvasErrorCode.INVALID_CURSOR), 422),
        (CanvasException(CanvasErrorCode.UNAVAILABLE), 503),
        (AuthException(AuthErrorCode.USER_NOT_FOUND), 404),
    ],
)
def test_feed_propagates_declared_errors(feed_api, error, status):
    client, service = feed_api
    service.list.side_effect = error
    response = client.get(PATHS[0])
    assert response.status_code == status and response.json()["detail"]["error"] == error.code.error


def encode(value):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@pytest.fixture
def valid_cursor():
    return {
        "v": 1,
        "domain": "canvas-publication-feed",
        "scope": "plaza",
        "sort": "latest",
        "filter_hash": CanvasFeedService._filter_hash(CanvasFeedQuery()),
        "published_at": "2026-11-03T12:00:00.123456Z",
        "canvas_id": CANVAS,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"v": True},
        {"v": "1"},
        {"v": 2},
        {"domain": "boards"},
        {"sort": "popular"},
        {"scope": "board:" + BOARD},
        {"filter_hash": "0" * 64},
        {"extra": True},
        {"canvas_id": True},
        {"canvas_id": "invalid"},
        {"published_at": True},
        {"published_at": 1780000000},
        {"published_at": "2026-11-03T12:00:00"},
        {"published_at": "2026-11-03T12:00:00+09:00"},
        {"published_at": "2026-02-30T00:00:00Z"},
        {"published_at": "2026-11-03T12:00:00.1234567Z"},
    ],
)
def test_cursor_rejects_wrong_domain_scope_filters_types_extra_and_dates(valid_cursor, change):
    value = encode({**valid_cursor, **change})
    with pytest.raises(CanvasException) as error:
        CanvasFeedService._before(value, "plaza", valid_cursor["filter_hash"])
    assert error.value.code == CanvasErrorCode.INVALID_CURSOR.code


@pytest.mark.parametrize(
    "cursor",
    ["%%%", "a", "e30=", "e30 ", "x" * 2049, encode(b"\xff"), encode([]), encode(b'{"v":1,"v":1}')],
)
def test_cursor_rejects_garbage_duplicate_keys_and_noncanonical_encoding(cursor, valid_cursor):
    with pytest.raises(CanvasException):
        CanvasFeedService._before(cursor, "plaza", valid_cursor["filter_hash"])


def test_cursor_preserves_microsecond_ties_and_binds_normalized_filters(valid_cursor):
    before = CanvasFeedService._before(encode(valid_cursor), "plaza", valid_cursor["filter_hash"])
    assert before[0].microsecond == 123456 and before[1] == UUID(CANVAS)
    base = CanvasFeedService._filter_hash(CanvasFeedQuery())
    assert CanvasFeedService._filter_hash(CanvasFeedQuery(limit=100, cursor="x")) == base
    for query in (
        CanvasFeedQuery(board_id=BOARD),
        CanvasFeedQuery(shelf_id=SHELF),
        CanvasFeedQuery(interest_id="ai"),
        CanvasFeedQuery(tag_id=TAG),
    ):
        with pytest.raises(CanvasException):
            CanvasFeedService._before(
                encode(valid_cursor), "plaza", CanvasFeedService._filter_hash(query)
            )
