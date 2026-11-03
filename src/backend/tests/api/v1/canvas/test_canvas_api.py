import asyncio
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.canvas import (
    CanvasContent,
    CanvasDocumentResponse,
    CanvasDocumentSaveResponse,
    CanvasResponse,
)
from app.routers.v1.canvas import MAX_CANVAS_DOCUMENT_REQUEST_BYTES, router
from app.services.canvas import CanvasService
from tests.fixtures.canvas_document_data import canvas_document

pytestmark = pytest.mark.api_test
BOARD = "00000000-0000-0000-0000-000000000001"
SHELF = "00000000-0000-0000-0000-000000000002"
CANVAS = "00000000-0000-0000-0000-000000000003"
PATH = f"/api/v1/canvases/{CANVAS}"
CREATE_PATH = f"/api/v1/boards/{BOARD}/canvases"
METADATA = {
    "id": CANVAS,
    "board_id": BOARD,
    "shelf_id": SHELF,
    "author_id": 1,
    "title": "초안",
    "summary": "",
    "status": "draft",
    "visibility": "members",
    "revision": 0,
    "trashed_at": None,
    "created_at": "2026-10-29T00:00:00Z",
    "updated_at": "2026-10-29T00:00:00Z",
}
DATA = {
    "canvas": METADATA,
    "view": "draft",
    "document_revision": 0,
    "capabilities": {
        "read_document": True,
        "edit_metadata": True,
        "edit_document": True,
        "trash": True,
        "restore": False,
    },
}
OPERATIONS = [
    ("POST", CREATE_PATH, {"shelf_id": SHELF, "title": "초안"}, "create", 201),
    ("GET", PATH, None, "get", 200),
    ("GET", PATH + "/document", None, "document", 200),
    (
        "PUT",
        PATH + "/document",
        {"expected_revision": 0, "document": {}},
        "save_document",
        200,
    ),
    ("PATCH", PATH, {"expected_revision": 0, "title": "수정"}, "change", 200),
    ("DELETE", PATH, {"expected_revision": 0}, "trash", 204),
    ("POST", PATH + "/restore", {"expected_revision": 0}, "restore", 200),
]


@pytest.fixture
def canvas_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=CanvasService)
    app.dependency_overrides[CanvasService] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize("method,path,body,operation,status", OPERATIONS)
def test_canvas_router_success_contract(canvas_api, method, path, body, operation, status):
    client, service = canvas_api
    result = (
        1
        if operation == "trash"
        else CanvasDocumentResponse(document=CanvasContent(), revision=0)
        if operation == "document"
        else CanvasDocumentSaveResponse(revision=1)
        if operation == "save_document"
        else CanvasResponse(**DATA)
    )
    getattr(service, operation).return_value = result
    response = client.request(method, path, json=body)
    assert response.status_code == status, response.text
    assert response.headers["cache-control"] == "private, no-store"
    if status == 204:
        assert response.content == b"" and response.headers["x-canvas-revision"] == "1"
    else:
        assert response.json() == result.model_dump(mode="json")
    if status == 201:
        assert response.headers["location"] == PATH
    getattr(service, operation).assert_awaited_once()


def test_document_route_serializes_typed_engine_objects_and_layer_order(canvas_api):
    client, service = canvas_api
    fixture = Path(__file__).parents[3] / "fixtures" / "canvas_content_v1.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    service.document.return_value = CanvasDocumentResponse(
        document=CanvasContent.model_validate(raw), revision=0
    )
    response = client.get(PATH + "/document")
    assert response.status_code == 200
    assert response.json() == {"document": raw, "revision": 0, "view": "draft"}
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize("method,path,body,operation,status", OPERATIONS)
def test_all_draft_routes_require_session(canvas_api, method, path, body, operation, status):
    client, service = canvas_api
    client.app.dependency_overrides.pop(get_current_session_user)
    assert client.request(method, path, json=body).status_code == 401
    getattr(service, operation).assert_not_awaited()


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"title": None},
        {"title": " "},
        {"title": "a" * 201},
        {"summary": None},
        {"summary": "a" * 501},
        {"shelf_id": None},
        {"shelf_id": "invalid"},
        {"visibility": None},
        {"visibility": "private"},
        {"author_id": 2},
        {"board_id": BOARD},
        {"status": "published"},
        {"status": "trashed"},
        {"tag_ids": []},
        {"thumbnail_asset_id": SHELF},
        {"published_at": "2026-10-29T00:00:00Z"},
        {"document": {}},
        {"expected_document_revision": 0},
    ],
)
def test_canvas_patch_accepts_only_supported_metadata_fields(canvas_api, changes):
    client, service = canvas_api
    response = client.patch(PATH, json={"expected_revision": 0, **changes})
    assert response.status_code == 422, response.text
    service.change.assert_not_awaited()


@pytest.mark.parametrize("revision", [-1, 2**63, True, 1.5, "1"])
def test_metadata_revision_uses_strict_database_integer_range(canvas_api, revision):
    client, service = canvas_api
    assert (
        client.patch(PATH, json={"expected_revision": revision, "title": "변경"}).status_code == 422
    )
    service.change.assert_not_awaited()


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "draft"},
        {"author_id": 1},
        {"board_id": BOARD},
        {"title": " "},
        {"document": {}},
        {"visibility": "invalid"},
    ],
)
def test_canvas_creation_rejects_invalid_and_server_owned_fields(canvas_api, fields):
    client, service = canvas_api
    response = client.post(CREATE_PATH, json={"shelf_id": SHELF, "title": "초안", **fields})
    assert response.status_code == 422
    service.create.assert_not_awaited()


@pytest.mark.parametrize("suffix,operation", [("", "get"), ("/document", "document")])
def test_unimplemented_publication_view_is_not_exposed(canvas_api, suffix, operation):
    client, service = canvas_api
    assert client.get(PATH + suffix, params={"view": "publication"}).status_code == 422
    getattr(service, operation).assert_not_awaited()


@pytest.mark.parametrize("revision", [-1, 2**63, True, 1.5, "1", None])
def test_document_revision_requires_strict_database_integer(canvas_api, revision):
    client, service = canvas_api
    response = client.put(PATH + "/document", json={"expected_revision": revision, "document": {}})
    assert response.status_code == 422
    service.save_document.assert_not_awaited()


@pytest.mark.parametrize(
    "fields",
    [
        {"document": None},
        {"document": {"schema_version": 2}},
        {"document": {"files": {}}},
        {"expected_document_revision": 0},
        {"title": "제목은 메타데이터"},
        {"view": "publication"},
    ],
)
def test_document_save_validates_schema_and_rejects_extra_fields(canvas_api, fields):
    client, service = canvas_api
    response = client.put(
        PATH + "/document", json={"expected_revision": 0, "document": {}, **fields}
    )
    assert response.status_code == 422
    service.save_document.assert_not_awaited()


def test_normalized_document_byte_limit_is_validation_error_below_transport_limit(canvas_api):
    client, service = canvas_api
    document = canvas_document()
    template = document["nodes"][0]
    document["nodes"], document["edges"] = [], []
    for index in range(18):
        node = deepcopy(template)
        node["id"] = node["engine_element"]["id"] = f"text-{index}"
        node["engine_element"]["text"] = node["engine_element"]["originalText"] = "한" * 19_500
        document["nodes"].append(node)
    document["element_order"] = [node["id"] for node in document["nodes"]]
    body = json.dumps({"expected_revision": 0, "document": document}, ensure_ascii=False).encode()
    assert len(body) < MAX_CANVAS_DOCUMENT_REQUEST_BYTES
    response = client.put(
        PATH + "/document", content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    service.save_document.assert_not_awaited()


def test_raw_request_limit_accepts_exact_boundary_and_replays_normal_body_dto(canvas_api):
    client, service = canvas_api
    service.save_document.return_value = CanvasDocumentSaveResponse(revision=1)
    body = b'{"expected_revision":0,"document":{}}'
    body += b" " * (MAX_CANVAS_DOCUMENT_REQUEST_BYTES - len(body))
    response = client.put(
        PATH + "/document", content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    form = service.save_document.await_args.args[2]
    assert form.expected_revision == 0 and form.document == CanvasContent()


@pytest.mark.parametrize("declared_length", [None, "1"])
def test_chunked_and_false_length_are_counted_before_json_decode(canvas_api, declared_length):
    client, service = canvas_api
    consumed, sent = [], []
    chunks = [b"x" * (64 * 1024)] * 33 + [b"x", b"must not be read"]

    async def receive():
        index = len(consumed)
        consumed.append(index)
        return {"type": "http.request", "body": chunks[index], "more_body": index < len(chunks) - 1}

    async def send(message):
        sent.append(message)

    headers = [(b"content-type", b"application/json")]
    if declared_length is not None:
        headers.append((b"content-length", declared_length.encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "PUT",
        "scheme": "http",
        "path": PATH + "/document",
        "raw_path": (PATH + "/document").encode(),
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 123),
        "server": ("testserver", 80),
        "root_path": "",
    }
    asyncio.run(client.app(scope, receive, send))
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"])["detail"]["error"] == "CANVAS_DOCUMENT_TOO_LARGE"
    assert len(consumed) == 34
    service.save_document.assert_not_awaited()


@pytest.mark.parametrize(
    "error,status",
    [
        (CanvasException(CanvasErrorCode.DOCUMENT_CONFLICT, {"current_revision": 9}), 409),
        (CanvasException(CanvasErrorCode.INVALID_STATE), 409),
        (CanvasException(CanvasErrorCode.FORBIDDEN), 403),
        (CanvasException(CanvasErrorCode.NOT_FOUND), 404),
        (CanvasException(CanvasErrorCode.UNAVAILABLE), 503),
        (AssetException(AssetErrorCode.INVALID_REFERENCE), 422),
    ],
)
def test_document_save_propagates_declared_domain_errors(canvas_api, error, status):
    client, service = canvas_api
    service.save_document.side_effect = error
    response = client.put(PATH + "/document", json={"expected_revision": 0, "document": {}})
    assert response.status_code == status
    assert response.json()["detail"]["error"] == error.code.error
    if error.code == CanvasErrorCode.DOCUMENT_CONFLICT.code:
        assert response.json()["detail"]["details"] == {"current_revision": 9}


def test_document_save_openapi_preserves_asset_and_request_validation_422(canvas_api):
    client, _ = canvas_api
    operation = client.app.openapi()["paths"]["/api/v1/canvases/{canvas_id}/document"]["put"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/CanvasDocumentSaveForm"
    )
    assert {"200", "401", "403", "404", "409", "413", "422", "503"} <= operation["responses"].keys()
    schema = operation["responses"]["422"]["content"]["application/json"]["schema"]
    assert {item["$ref"] for item in schema["anyOf"]} == {
        "#/components/schemas/AssetErrorResponse",
        "#/components/schemas/CanvasDocumentValidationErrorResponse",
    }
