"""Comment validation and current-session transport boundaries."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.canvas_comment import CommentCapabilities, CommentPage, CommentResponse
from app.routers.v1.canvas import router
from app.services.canvas_comment import CanvasCommentService

pytestmark = pytest.mark.api_test
PATH = f"/api/v1/canvases/{UUID(int=1)}/comments"


@pytest.fixture
def api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    service = AsyncMock(spec=CanvasCommentService)
    row = CommentResponse(
        id=UUID(int=2),
        canvas_id=UUID(int=1),
        author_id=sample_user.id,
        body="댓글",
        status="visible",
        revision=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        capabilities=CommentCapabilities(edit=True, delete=True, moderate=False),
    )
    service.get.return_value = service.create.return_value = service.change.return_value = row
    service.list.return_value = CommentPage(items=[row], can_create=True)
    app.dependency_overrides[CanvasCommentService] = lambda: service
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    app.dependency_overrides[get_current_token_user] = lambda: sample_user
    return TestClient(app), service


def test_crud_and_optional_get_contract(api):
    client, service = api
    created = client.post(PATH, json={"body": "  댓글  "})
    assert created.status_code == 201 and created.headers["cache-control"] == "private, no-store"
    assert service.create.await_args.args[-1].body == "댓글"
    path = created.headers["location"]
    assert client.get(PATH).json()["items"][0]["body"] == "댓글"
    assert client.get(path).status_code == 200
    assert client.patch(path, json={"expected_revision": 0, "body": "새 댓글"}).status_code == 200
    assert client.request("DELETE", path, json={"expected_revision": 0}).status_code == 200
    assert service.change.await_args.kwargs == {"delete": True}
    paths = client.app.openapi()["paths"]
    assert {} in paths["/api/v1/canvases/{canvas_id}/comments"]["get"]["security"]


@pytest.mark.parametrize(
    "body", [{"body": " "}, {"body": None}, {"body": "x" * 5001}, {"body": "ok", "author_id": 1}]
)
def test_invalid_create(api, body):
    client, service = api
    assert client.post(PATH, json=body).status_code == 422
    service.create.assert_not_awaited()


@pytest.mark.parametrize(
    "body",
    [
        {"expected_revision": True, "body": "x"},
        {"expected_revision": 0},
        {"expected_revision": 0, "body": None},
        {"expected_revision": 0, "status": "deleted", "reason": "삭제"},
        {"expected_revision": 0, "status": "hidden"},
        {"expected_revision": 0, "status": "hidden", "reason": " "},
        {"expected_revision": 0, "status": "hidden", "reason": "숨김", "body": "x"},
    ],
)
def test_patch_requires_one_valid_operation(api, body):
    client, service = api
    assert client.patch(PATH + f"/{UUID(int=2)}", json=body).status_code == 422
    service.change.assert_not_awaited()


def test_writes_require_session(api):
    client, service = api
    del client.app.dependency_overrides[get_current_session_user]
    del client.app.dependency_overrides[get_current_token_user]
    for method, path, body in [
        ("POST", PATH, {"body": "댓글"}),
        ("PATCH", PATH + f"/{UUID(int=2)}", {"expected_revision": 0, "body": "수정"}),
        ("DELETE", PATH + f"/{UUID(int=2)}", {"expected_revision": 0}),
    ]:
        assert (
            client.request(method, path, json=body, headers={"X-API-Key": "key"}).status_code == 401
        )
    service.create.assert_not_awaited()
    service.change.assert_not_awaited()
