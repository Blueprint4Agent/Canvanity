from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.tag_exception import TagErrorCode, TagException
from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.tag import TagCatalogResponse, TagCreationResult, TagResponse
from app.routers.v1.tag import router
from app.services.tag import TagService

pytestmark = pytest.mark.api_test
TAG = TagResponse(id=UUID("00000000-0000-0000-0000-000000000001"), name="C++")


@pytest.fixture
def tag_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/tags")
    service = AsyncMock(spec=TagService)
    app.dependency_overrides[TagService] = lambda: service
    return TestClient(app), service, sample_user


def test_public_search_has_only_tag_summary_and_bounded_query(tag_api):
    client, service, _ = tag_api
    service.search.return_value = TagCatalogResponse(items=[TAG])
    result = client.get("/api/v1/tags", params={"q": " C++ ", "limit": 5})
    assert result.status_code == 200
    assert result.json() == {"items": [{"id": str(TAG.id), "name": "C++"}]}
    query = service.search.call_args.args[0]
    assert query.q == "C++" and query.limit == 5
    operation = client.app.openapi()["paths"]["/api/v1/tags"]["get"]
    assert "security" not in operation


@pytest.mark.parametrize("created,status", [(True, 201), (False, 200)])
def test_create_and_reuse_require_session_and_preserve_same_response(tag_api, created, status):
    client, service, user = tag_api
    assert client.post("/api/v1/tags", json={"name": "C++"}).status_code == 401
    service.create.assert_not_awaited()
    client.app.dependency_overrides[get_current_session_user] = lambda: user
    service.create.return_value = TagCreationResult(TAG, created)
    result = client.post("/api/v1/tags", json={"name": " C++ "})
    assert result.status_code == status
    assert result.json() == {"id": str(TAG.id), "name": "C++"}
    assert result.headers["cache-control"] == "private, no-store"
    assert service.create.call_args.args[0] == user.id
    assert service.create.call_args.args[1].name == "C++"


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 51}, {"q": "a" * 41}, {"q": "a\n"}, {"canvas_id": "hidden"}]
)
def test_search_rejects_invalid_and_unrecognized_query_parameters(tag_api, params):
    client, service, _ = tag_api
    assert client.get("/api/v1/tags", params=params).status_code == 422
    service.search.assert_not_awaited()


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": None},
        {"name": " "},
        {"name": "a\u200b"},
        {"name": "x", "normalized_name": "server-owned"},
    ],
)
def test_create_validates_name_and_only_client_owned_field(tag_api, body):
    client, service, user = tag_api
    client.app.dependency_overrides[get_current_session_user] = lambda: user
    assert client.post("/api/v1/tags", json=body).status_code == 422
    service.create.assert_not_awaited()


def test_tag_storage_failure_is_domain_503_for_both_routes(tag_api):
    client, service, user = tag_api
    client.app.dependency_overrides[get_current_session_user] = lambda: user
    for method, kwargs, operation in [
        ("GET", {}, "search"),
        ("POST", {"json": {"name": "C#"}}, "create"),
    ]:
        getattr(service, operation).side_effect = TagException(TagErrorCode.UNAVAILABLE)
        result = client.request(method, "/api/v1/tags", **kwargs)
        assert result.status_code == 503 and result.json()["detail"]["error"] == "TAG_UNAVAILABLE"
