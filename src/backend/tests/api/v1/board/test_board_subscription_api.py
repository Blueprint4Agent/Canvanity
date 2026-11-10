"""Subscription transport is session-only and independent of membership."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.board import BoardSubscriptionResponse
from app.models.canvas_feed import CanvasFeedResponse
from app.routers.v1.board import router as board_router
from app.routers.v1.canvas import router as canvas_router
from app.services.board_subscription import BoardSubscriptionService
from app.services.canvas_feed import CanvasFeedService

pytestmark = pytest.mark.api_test
ID = UUID(int=1)
PATH = f"/api/v1/boards/{ID}/subscription"
FEED = "/api/v1/me/subscriptions/canvases"


@pytest.fixture
def api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(board_router, prefix="/api/v1/boards")
    app.include_router(canvas_router, prefix="/api/v1")
    subscriptions = AsyncMock(spec=BoardSubscriptionService)
    subscriptions.get.return_value = subscriptions.set.return_value = BoardSubscriptionResponse(
        subscribed=True
    )
    feed = AsyncMock(spec=CanvasFeedService)
    feed.list.return_value = CanvasFeedResponse(items=[])
    app.dependency_overrides[BoardSubscriptionService] = lambda: subscriptions
    app.dependency_overrides[CanvasFeedService] = lambda: feed
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    return TestClient(app), subscriptions, feed


def test_delegation_scope_cache_and_contract(api, sample_user):
    client, service, feed = api
    for method in ("GET", "PUT", "DELETE"):
        response = client.request(method, PATH)
        assert (
            response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
        )
        assert response.json() == {"subscribed": True}
        if method == "GET":
            service.get.assert_awaited_with(sample_user.id, ID)
        else:
            service.set.assert_awaited_with(sample_user.id, ID, subscribed=method == "PUT")
    assert client.get(FEED).json() == {"items": [], "next_cursor": None}
    assert feed.list.await_args.kwargs == {
        "scope": f"subscriptions:{sample_user.id}",
        "subscribed": True,
    }
    paths = client.app.openapi()["paths"]
    for path, methods in [
        ("/api/v1/boards/{board_id}/subscription", ("get", "put", "delete")),
        (FEED, ("get",)),
    ]:
        for method in methods:
            assert paths[path][method]["security"] == [{"OAuth2PasswordBearer": []}]


def test_reject_key_and_invalid_query(api):
    client, service, feed = api
    for query in ({"limit": 0}, {"status": "all"}, {"board_id": str(ID)}):
        assert client.get(FEED, params=query).status_code == 422
    feed.list.assert_not_awaited()
    del client.app.dependency_overrides[get_current_session_user]
    for method, path in [("GET", PATH), ("PUT", PATH), ("DELETE", PATH), ("GET", FEED)]:
        assert client.request(method, path, headers={"X-API-Key": "key"}).status_code == 401
    service.set.assert_not_awaited()
