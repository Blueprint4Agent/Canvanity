from copy import deepcopy
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.board_layout import BoardLayoutDocument
from app.routers.v1.board import router
from app.services.board_layout import BoardLayoutService
from app.utils.board_layout_limits import MAX_BOARD_LAYOUT_REQUEST_BYTES

pytestmark = pytest.mark.api_test
BOARD = str(UUID(int=1))
WIDGET = {
    "id": "latest",
    "type": "canvas_collection",
    "position": {"x": 100, "y": -100},
    "size": {"width": 600, "height": 300},
    "source": {"board_id": BOARD, "sort": "latest", "limit": 6},
}


@pytest.fixture
def layout_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=BoardLayoutService)
    service.save.return_value = service.get.return_value = {
        "board_id": BOARD,
        "document": {"schema_version": 1, "widgets": [WIDGET]},
        "layout_revision": 0,
    }
    app.dependency_overrides[BoardLayoutService] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize(
    "field,value",
    [
        ("type", "html"),
        ("id", ""),
        ("id", "한글"),
        ("id", "x" * 81),
        ("position", {"x": True, "y": 0}),
        ("position", {"x": "2", "y": 0}),
        ("position", {"x": float("inf"), "y": 0}),
        ("position", {"x": float("nan"), "y": 0}),
        ("position", {"x": 100001, "y": 0}),
        ("size", {"width": 0, "height": 2}),
        ("size", {"width": 2, "height": -1}),
        ("size", {"width": True, "height": 2}),
        ("size", {"width": 2, "height": 100001}),
        ("source", {"board_id": BOARD, "limit": True}),
        ("source", {"board_id": BOARD, "limit": "6"}),
        ("source", {"board_id": BOARD, "limit": 0}),
        ("source", {"board_id": BOARD, "limit": 21}),
        ("source", {"board_id": BOARD, "sort": "sql"}),
        ("source", {"board_id": BOARD, "url": "https://example.com"}),
        ("source", {"board_id": BOARD, "asset_id": str(UUID(int=9))}),
        ("source", {"board_id": BOARD, "shelf_id": "invalid"}),
        ("html", "<script>1</script>"),
    ],
)
def test_strict_widget_document(field, value):
    widget = deepcopy(WIDGET)
    widget[field] = value
    with pytest.raises(ValidationError):
        BoardLayoutDocument.model_validate({"schema_version": 1, "widgets": [widget]})


@pytest.mark.parametrize(
    "document",
    [
        {"schema_version": True, "widgets": []},
        {"schema_version": "1", "widgets": []},
        {"schema_version": 2, "widgets": []},
        {"schema_version": 1, "widgets": [WIDGET, WIDGET]},
        {"schema_version": 1, "widgets": [], "nodes": []},
        {"engine": "excalidraw", "nodes": [], "edges": []},
        {"schema_version": 1, "widgets": [dict(WIDGET, id=str(n)) for n in range(101)]},
    ],
)
def test_document_version_content_and_count(document):
    with pytest.raises(ValidationError):
        BoardLayoutDocument.model_validate(document)


def test_all_four_types_and_semantic_bytes(monkeypatch):
    widgets = [WIDGET] + [
        {k: v for k, v in dict(WIDGET, id=kind, type=kind).items() if k != "source"}
        for kind in ("board_intro", "shelf_navigation", "board_cover")
    ]
    doc = {"schema_version": 1, "widgets": widgets}
    canonical = BoardLayoutDocument.model_validate(doc).canonical_bytes()
    monkeypatch.setattr("app.models.board_layout.MAX_BOARD_LAYOUT_BYTES", len(canonical))
    BoardLayoutDocument.model_validate(doc)
    monkeypatch.setattr("app.models.board_layout.MAX_BOARD_LAYOUT_BYTES", len(canonical) - 1)
    with pytest.raises(ValidationError):
        BoardLayoutDocument.model_validate(doc)
    for kind in ("board_intro", "shelf_navigation", "board_cover"):
        with pytest.raises(ValidationError):
            BoardLayoutDocument.model_validate(
                {
                    "schema_version": 1,
                    "widgets": [dict(WIDGET, type=kind)],
                }
            )


@pytest.mark.parametrize("revision", [True, "0", 0.0, -1, 2**31])
def test_strict_revision_rejected_before_service(layout_api, revision):
    client, service = layout_api
    response = client.put(
        f"/api/v1/boards/{BOARD}/layout",
        json={
            "expected_revision": revision,
            "reason": "검증",
            "document": {
                "schema_version": 1,
                "widgets": [WIDGET],
            },
        },
    )
    assert response.status_code == 422
    service.save.assert_not_called()


def test_management_roundtrip_and_raw_preparse_limit(layout_api):
    client, service = layout_api
    path = f"/api/v1/boards/{BOARD}/layout"
    got = client.get(path)
    assert got.status_code == 200 and got.headers["cache-control"] == "private, no-store"
    saved = client.put(
        path,
        json={
            "expected_revision": 0,
            "reason": "그대로 저장",
            "document": got.json()["document"],
        },
    )
    assert saved.status_code == 200 and saved.json() == got.json()
    service.save.reset_mock()
    oversized = client.put(path, content=b"{" + b" " * MAX_BOARD_LAYOUT_REQUEST_BYTES)
    assert oversized.status_code == 413
    assert oversized.json()["detail"]["error"] == "BOARD_LAYOUT_TOO_LARGE"
    service.save.assert_not_called()
