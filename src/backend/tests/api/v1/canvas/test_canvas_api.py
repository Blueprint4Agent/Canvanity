from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.canvas import CanvasContent, CanvasDocumentResponse, CanvasResponse
from app.routers.v1.canvas import router
from app.services.canvas import CanvasService

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
    "capabilities": {"read_document": True, "edit_metadata": True, "trash": True, "restore": False},
}
OPERATIONS = [
    ("POST", CREATE_PATH, {"shelf_id": SHELF, "title": "초안"}, "create", 201),
    ("GET", PATH, None, "get", 200),
    ("GET", PATH + "/document", None, "document", 200),
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
