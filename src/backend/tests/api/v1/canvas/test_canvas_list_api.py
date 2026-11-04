"""Owner list transport, authentication, strict query and cursor contracts."""

import base64
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.canvas_list import CanvasListQuery, CanvasListResponse
from app.routers.v1.canvas import router
from app.services.canvas_list import CanvasListService

pytestmark = pytest.mark.api_test
PATH = "/api/v1/me/canvases"
AT = datetime(2026, 11, 4, 0, 0, 0, 123456, tzinfo=UTC)


@pytest.fixture
def list_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    service = AsyncMock(spec=CanvasListService)
    service.list.return_value = CanvasListResponse(items=[], as_of=AT)
    app.dependency_overrides[CanvasListService] = lambda: service
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    return TestClient(app), service


def test_list_session_identity_defaults_cache_and_openapi(list_api, sample_user):
    client, service = list_api
    response = client.get(PATH)
    assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
    assert response.json() == {
        "items": [],
        "as_of": AT.isoformat().replace("+00:00", "Z"),
        "next_cursor": None,
    }
    assert service.list.await_args.args == (sample_user.id, CanvasListQuery())
    operation = client.app.openapi()["paths"][PATH]["get"]
    assert operation["security"] == [{"OAuth2PasswordBearer": []}]
    assert {"200", "401", "404", "422", "503"} <= operation["responses"].keys()
    schema = operation["responses"]["422"]["content"]["application/json"]["schema"]
    assert {value["$ref"] for value in schema["anyOf"]} == {
        "#/components/schemas/CanvasErrorResponse",
        "#/components/schemas/CanvasMetadataValidationErrorResponse",
    }
    params = {
        "status": "all",
        "publication": "unpublished",
        "board_id": str(UUID(int=2)),
        "shelf_id": str(UUID(int=3)),
        "limit": 100,
        "sort": "last_modified",
        "cursor": "valid-cursor",
    }
    assert client.get(PATH, params=params).status_code == 200
    assert service.list.await_args.args[1] == CanvasListQuery(**params)


@pytest.mark.parametrize(
    "params",
    [
        {"status": "published"},
        {"status": "DRAFT"},
        {"publication": "draft"},
        {"sort": "latest"},
        {"board_id": "wrong"},
        {"shelf_id": "wrong"},
        {"limit": 0},
        {"limit": 101},
        {"limit": 1.5},
        {"limit": "true"},
        {"cursor": ""},
        {"cursor": "x" * 2049},
        {"author_id": 7},
        {"user_id": 7},
        {"q": "private"},
    ],
)
def test_list_invalid_query_never_calls_service(list_api, params):
    client, service = list_api
    assert client.get(PATH, params=params).status_code == 422
    service.list.assert_not_awaited()


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-API-Key": "not-a-session"},
        {"Authorization": "Bearer wrong"},
        {"X-API-Key": "key", "Authorization": "Bearer wrong"},
    ],
)
def test_list_requires_bearer_and_rejects_bad_bearer_or_key(list_api, headers):
    client, service = list_api
    del client.app.dependency_overrides[get_current_session_user]
    response = client.get(PATH, headers=headers)
    assert response.status_code == 401 and response.json()["detail"]["error"] == "INVALID_TOKEN"
    service.list.assert_not_awaited()


@pytest.mark.parametrize(
    "error,status",
    [
        (CanvasException(CanvasErrorCode.NOT_FOUND), 404),
        (CanvasException(CanvasErrorCode.INVALID_CURSOR), 422),
        (CanvasException(CanvasErrorCode.UNAVAILABLE), 503),
        (AuthException(AuthErrorCode.USER_NOT_FOUND), 404),
    ],
)
def test_list_domain_errors_are_declared_and_propagated(list_api, error, status):
    client, service = list_api
    service.list.side_effect = error
    response = client.get(PATH)
    assert response.status_code == status and response.json()["detail"]["error"] == error.code.error


def encode(value):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@pytest.fixture
def cursor_payload():
    return {
        "v": 1,
        "domain": "canvas-owner-list",
        "user_id": 7,
        "sort": "last_modified",
        "filter_hash": CanvasListService._filter_hash(CanvasListQuery()),
        "last_modified_at": AT.isoformat(),
        "canvas_id": str(UUID(int=3)),
    }


@pytest.mark.parametrize(
    "change",
    [
        {"v": True},
        {"v": "1"},
        {"v": 2},
        {"domain": "canvas-publication-feed"},
        {"user_id": 8},
        {"user_id": True},
        {"user_id": "7"},
        {"sort": "latest"},
        {"filter_hash": "0" * 64},
        {"extra": 1},
        {"canvas_id": True},
        {"canvas_id": "wrong"},
        {"last_modified_at": True},
        {"last_modified_at": 1780000000},
        {"last_modified_at": "2026-11-04T00:00:00"},
        {"last_modified_at": "2026-11-04T00:00:00+09:00"},
        {"last_modified_at": "2026-02-30T00:00:00Z"},
        {"last_modified_at": "2026-11-04T00:00:00.1234567Z"},
    ],
)
def test_cursor_binds_domain_version_user_filters_sort_types_and_utc(cursor_payload, change):
    with pytest.raises(CanvasException) as error:
        CanvasListService._before(
            encode({**cursor_payload, **change}), 7, cursor_payload["filter_hash"]
        )
    assert error.value.code == CanvasErrorCode.INVALID_CURSOR.code


@pytest.mark.parametrize(
    "value",
    ["%%%", "a", "e30=", "e30 ", "x" * 2049, encode(b"\xff"), encode([]), encode(b'{"v":1,"v":1}')],
)
def test_cursor_rejects_garbage_extra_and_duplicate_json(value, cursor_payload):
    with pytest.raises(CanvasException):
        CanvasListService._before(value, 7, cursor_payload["filter_hash"])


def test_cursor_preserves_tie_and_limit_change_but_rejects_changed_normalized_filters(
    cursor_payload,
):
    query = CanvasListQuery()
    value = encode(cursor_payload)
    assert CanvasListService._before(value, 7, cursor_payload["filter_hash"]) == (AT, UUID(int=3))
    assert CanvasListService._filter_hash(
        CanvasListQuery(limit=100, cursor="x")
    ) == CanvasListService._filter_hash(query)
    for query in (
        CanvasListQuery(status="all"),
        CanvasListQuery(publication="published"),
        CanvasListQuery(board_id=UUID(int=2)),
        CanvasListQuery(shelf_id=UUID(int=3)),
    ):
        with pytest.raises(CanvasException):
            CanvasListService._before(value, 7, CanvasListService._filter_hash(query))
