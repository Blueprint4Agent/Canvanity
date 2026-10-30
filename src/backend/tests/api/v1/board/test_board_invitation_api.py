from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.board import BoardMemberDetail, BoardMemberUpdateResponse
from app.routers.v1.board import router
from app.services.board_membership import BoardMembershipService

pytestmark = pytest.mark.api_test
PATH = "/api/v1/boards/00000000-0000-0000-0000-000000000001/members"


@pytest.fixture
def invitation_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=BoardMembershipService)
    app.dependency_overrides[BoardMembershipService] = lambda: service
    return TestClient(app), service


def test_invitation_requires_bearer_authentication():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    response = TestClient(app).post(
        PATH, json={"user_id": 2, "expected_revision": 0, "reason": "등록"}
    )
    assert response.status_code == 401


def test_invitation_route_uses_member_detail_contract(invitation_api):
    client, service = invitation_api
    service.invite.return_value = BoardMemberUpdateResponse(
        member=BoardMemberDetail(
            user_id=2,
            name="초대 회원",
            handle=None,
            role="member",
            status="active",
            grade_id=UUID("00000000-0000-0000-0000-000000000002"),
            grade_name="뉴커머",
            grade_rank=0,
            joined_at=datetime(2026, 10, 28, tzinfo=UTC),
        ),
        board_revision=1,
    )
    response = client.post(
        PATH, json={"user_id": 2, "expected_revision": 0, "reason": "  수동 등록  "}
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == service.invite.return_value.model_dump(mode="json")
    service.invite.assert_awaited_once()
    assert service.invite.call_args.args[2].reason == "수동 등록"


@pytest.mark.parametrize(
    "changes",
    [
        {"user_id": 0},
        {"user_id": -1},
        {"user_id": 2**31},
        {"user_id": True},
        {"user_id": 1.5},
        {"user_id": "2"},
        {"user_id": None},
        {"expected_revision": -1},
        {"reason": " "},
        {"reason": "a" * 501},
        {"role": "admin"},
        {"status": "active"},
        {"grade_id": "00000000-0000-0000-0000-000000000002"},
        {"email": "invite@example.com"},
    ],
)
def test_invitation_rejects_unsupported_fields_and_invalid_input(invitation_api, changes):
    client, service = invitation_api
    response = client.post(
        PATH, json={"user_id": 2, "expected_revision": 0, "reason": "등록", **changes}
    )
    assert response.status_code == 422
    service.invite.assert_not_awaited()
