"""Public statistics and explicit session-bound daily-view transport."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.canvas_stats import CanvasStatsResponse, CanvasViewResponse
from app.routers.v1.canvas import router
from app.services.canvas_stats import CanvasStatsService

pytestmark = pytest.mark.api_test
ID = UUID(int=1)
PATH = f"/api/v1/canvases/{ID}"


@pytest.fixture
def api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    service = AsyncMock(spec=CanvasStatsService)
    at = datetime.now(UTC)
    stats = CanvasStatsResponse(
        like_count=1,
        comment_count=2,
        view_count=3,
        activity_score=6,
        window_started_on=at.date(),
        as_of=at,
    )
    service.get.return_value = stats
    service.record.return_value = CanvasViewResponse(recorded=True, stats=stats)
    app.dependency_overrides[CanvasStatsService] = lambda: service
    app.dependency_overrides[get_current_token_user] = lambda: None
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    return TestClient(app), service


def test_identity_cache_and_openapi(api, sample_user):
    client, service = api
    result = client.get(PATH + "/stats")
    assert result.status_code == 200 and result.headers["cache-control"] == "private, no-store"
    assert result.json()["view_count"] == 3 and result.json()["window_days"] == 30
    service.get.assert_awaited_once_with(None, ID)
    result = client.put(PATH + "/view")
    assert result.status_code == 200 and result.json()["recorded"]
    service.record.assert_awaited_once_with(sample_user.id, ID)
    paths = client.app.openapi()["paths"]
    assert {} in paths["/api/v1/canvases/{canvas_id}/stats"]["get"]["security"]
    assert paths["/api/v1/canvases/{canvas_id}/view"]["put"]["security"] == [
        {"OAuth2PasswordBearer": []}
    ]


def test_session_and_domain_failures(api):
    client, service = api
    del client.app.dependency_overrides[get_current_session_user]
    del client.app.dependency_overrides[get_current_token_user]
    assert client.put(PATH + "/view", headers={"X-API-Key": "key"}).status_code == 401
    service.record.assert_not_awaited()
    service.get.side_effect = CanvasException(CanvasErrorCode.NOT_FOUND)
    assert client.get(PATH + "/stats").status_code == 404
