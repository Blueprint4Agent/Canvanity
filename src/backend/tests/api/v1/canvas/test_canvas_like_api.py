"""Like transport delegates identity and preserves session/public-read boundaries."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.canvas import CanvasLikeResponse
from app.routers.v1.canvas import router
from app.services.canvas_like import CanvasLikeService

pytestmark = pytest.mark.api_test
ID = UUID(int=1)
PATH = f"/api/v1/canvases/{ID}/like"


@pytest.fixture
def api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    service = AsyncMock(spec=CanvasLikeService)
    service.get.return_value = service.set.return_value = CanvasLikeResponse(count=2, liked=True)
    app.dependency_overrides[CanvasLikeService] = lambda: service
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    app.dependency_overrides[get_current_token_user] = lambda: None
    return TestClient(app), service


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_delegation_cache_and_openapi(api, sample_user, method):
    client, service = api
    response = client.request(method, PATH)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == {"count": 2, "liked": True}
    if method == "GET":
        service.get.assert_awaited_once_with(None, ID)
    else:
        service.set.assert_awaited_once_with(sample_user.id, ID, liked=method == "PUT")
    operation = client.app.openapi()["paths"]["/api/v1/canvases/{canvas_id}/like"][method.lower()]
    assert operation["security"] == (
        [{"OAuth2PasswordBearer": []}, {}] if method == "GET" else [{"OAuth2PasswordBearer": []}]
    )
    assert {"200", "401", "404", "422", "503"} <= operation["responses"].keys()
    if method != "GET":
        assert "403" in operation["responses"]


@pytest.mark.parametrize("method", ["PUT", "DELETE"])
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "key"}, {"Authorization": "Bearer bad"}])
def test_write_requires_session(api, method, headers):
    client, service = api
    del client.app.dependency_overrides[get_current_session_user]
    assert client.request(method, PATH, headers=headers).status_code == 401
    service.set.assert_not_awaited()


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
@pytest.mark.parametrize("code", [CanvasErrorCode.NOT_FOUND, CanvasErrorCode.UNAVAILABLE])
def test_domain_failure(api, method, code):
    client, service = api
    service.get.side_effect = service.set.side_effect = CanvasException(code)
    response = client.request(method, PATH)
    assert response.status_code == code.code.status_code
    assert response.json()["detail"]["error"] == code.code.error
