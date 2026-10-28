from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.board import BoardOwnershipTransferResponse
from app.routers.v1.board import router
from app.services.board import BoardService

pytestmark = pytest.mark.api_test
PATH = "/api/v1/boards/00000000-0000-0000-0000-000000000001/ownership-transfer"


@pytest.fixture
def ownership_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=BoardService)
    app.dependency_overrides[BoardService] = lambda: service
    return TestClient(app), service


def test_ownership_requires_bearer():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    assert (
        TestClient(app)
        .post(PATH, json={"expected_revision": 0, "target_user_id": 2, "reason": "위임"})
        .status_code
        == 401
    )


def test_ownership_route_returns_explicit_receipt(ownership_api):
    client, service = ownership_api
    service.transfer_ownership.return_value = BoardOwnershipTransferResponse(
        board_id=UUID(PATH.split("/")[-2]),
        previous_owner_id=1,
        owner_id=2,
        board_revision=1,
    )
    response = client.post(
        PATH, json={"expected_revision": 0, "target_user_id": 2, "reason": "  위임  "}
    )
    assert response.status_code == 200
    assert response.json() == service.transfer_ownership.return_value.model_dump(mode="json")
    assert response.headers["cache-control"] == "private, no-store"
    assert service.transfer_ownership.call_args.args[2].reason == "위임"


@pytest.mark.parametrize(
    "changes",
    [
        {"target_user_id": 0},
        {"target_user_id": -1},
        {"target_user_id": 2**31},
        {"target_user_id": True},
        {"target_user_id": "2"},
        {"target_user_id": None},
        {"expected_revision": -1},
        {"reason": " "},
        {"reason": "a" * 501},
        {"role": "owner"},
        {"owner_id": 2},
        {"status": "active"},
    ],
)
def test_invalid_ownership_input_never_reaches_service(ownership_api, changes):
    client, service = ownership_api
    response = client.post(
        PATH, json={"expected_revision": 0, "target_user_id": 2, "reason": "위임", **changes}
    )
    assert response.status_code == 422
    service.transfer_ownership.assert_not_awaited()
