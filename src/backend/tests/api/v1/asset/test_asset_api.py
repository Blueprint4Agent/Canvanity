from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.asset import AssetResponse
from app.routers.v1.asset import router
from app.services.asset import AssetService

pytestmark = pytest.mark.api_test
CANVAS = "00000000-0000-0000-0000-000000000001"
ASSET = "00000000-0000-0000-0000-000000000002"
PATH = f"/api/v1/canvases/{CANVAS}/assets"
URL = f"{PATH}/{ASSET}"
DATA = dict(
    id=ASSET,
    canvas_id=CANVAS,
    content_type="image/webp",
    byte_size=24,
    width=10,
    height=12,
    frame_count=1,
    state="ready",
    expires_at=None,
    created_at="2026-10-29T00:00:00Z",
    url=URL,
)


@pytest.fixture
def asset_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=AssetService)
    app.dependency_overrides[AssetService] = lambda: service
    return TestClient(app), service


def test_upload_binary_read_and_deferred_delete_contract(asset_api):
    client, service = asset_api
    service.upload.return_value = AssetResponse(**DATA)
    service.read.return_value = b"normalized-webp"
    response = client.post(PATH, files={"file": ("image.png", b"png", "image/png")})
    assert (
        response.status_code == 201
        and response.json() == service.upload.return_value.model_dump(mode="json")
    )
    assert response.headers["location"] == URL
    assert response.headers["cache-control"] == "private, no-store"
    assert service.upload.await_args.args[:2] == (1, UUID(CANVAS))
    image = client.get(URL)
    assert image.status_code == 200 and image.content == b"normalized-webp"
    assert image.headers["content-type"] == "image/webp"
    assert image.headers["x-content-type-options"] == "nosniff"
    assert image.headers["cache-control"] == "private, no-store"
    assert ASSET in image.headers["content-disposition"]
    deleted = client.delete(URL)
    assert deleted.status_code == 204 and deleted.content == b""
    service.delete.assert_awaited_once_with(1, UUID(CANVAS), UUID(ASSET))
    content = client.app.openapi()["paths"]["/api/v1/canvases/{canvas_id}/assets/{asset_id}"][
        "get"
    ]["responses"]["200"]["content"]
    assert content == {"image/webp": {"schema": {"type": "string", "format": "binary"}}}


@pytest.mark.parametrize("method,path", [("POST", PATH), ("GET", URL), ("DELETE", URL)])
def test_images_require_session_bearer(asset_api, method, path):
    client, service = asset_api
    client.app.dependency_overrides.pop(get_current_session_user)
    response = client.request(method, path, files={"file": ("a.png", b"x")})
    assert response.status_code == 401
    assert not service.mock_calls


@pytest.mark.parametrize(
    "path,files", [(PATH, None), (PATH.replace(CANVAS, "invalid"), {"file": ("a", b"x")})]
)
def test_upload_requires_file_and_uuid(asset_api, path, files):
    client, service = asset_api
    assert client.post(path, files=files).status_code == 422
    service.upload.assert_not_awaited()
