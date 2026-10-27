from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.routers.v1.board import router
from app.services.board import BoardService

pytestmark = pytest.mark.api_test


def test_creation_rejects_unauthenticated_requests():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    assert (
        TestClient(app)
        .post("/api/v1/boards", json={"name": "Board", "slug": "test-board"})
        .status_code
        == 401
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"slug": "UPPER"},
        {"slug": "new"},
        {"interest_ids": ["ai"] * 2},
        {"interest_ids": ["a", "b", "c", "d"]},
        {"visibility": "private", "join_policy": "open"},
        {"owner_id": 999},
    ],
)
def test_creation_validates_public_contract_before_service(changes, sample_user):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=BoardService)
    app.dependency_overrides[BoardService] = lambda: service
    response = TestClient(app).post(
        "/api/v1/boards", json={"name": "Board", "slug": "test-board", **changes}
    )
    assert response.status_code == 422
    service.create.assert_not_called()
