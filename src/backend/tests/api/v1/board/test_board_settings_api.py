from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user
from app.main import register_exception_handlers
from app.models.board import (
    BOARD_SETTING_FIELDS,
    BoardSettingsPatchForm,
    BoardSummary,
    BoardUpdateResponse,
)
from app.routers.v1.board import router
from app.services.board import BoardService

pytestmark = pytest.mark.api_test
PATH = "/api/v1/boards/00000000-0000-0000-0000-000000000001"


@pytest.fixture
def settings_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    service = AsyncMock(spec=BoardService)
    app.dependency_overrides[BoardService] = lambda: service
    return TestClient(app), service


def test_settings_requires_bearer():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    assert (
        TestClient(app)
        .patch(PATH, json={"expected_revision": 0, "reason": "설정", "name": "보드"})
        .status_code
        == 401
    )


def test_settings_route_response_and_patch_contract(settings_api):
    client, service = settings_api
    service.update.return_value = BoardUpdateResponse(
        board=BoardSummary(
            id=UUID(PATH.rsplit("/", 1)[1]),
            owner_id=1,
            slug="board-settings",
            name="보드",
            description="",
            visibility="public",
            join_policy="open",
            status="active",
            revision=1,
            interest_ids=[],
            created_at=datetime(2026, 10, 28, tzinfo=UTC),
        ),
        rules="규칙",
        board_revision=1,
    )
    response = client.patch(
        PATH, json={"expected_revision": 0, "reason": "  관리  ", "rules": "규칙"}
    )
    assert response.status_code == 200, response.text
    assert response.json() == service.update.return_value.model_dump(mode="json")
    assert response.headers["cache-control"] == "private, no-store"
    assert service.update.call_args.args[2].reason == "관리"
    schema = BoardSettingsPatchForm.model_json_schema()
    assert schema["required"] == ["expected_revision", "reason"]
    assert [variant["required"] for variant in schema["allOf"][0]["anyOf"]] == [
        [field] for field in BOARD_SETTING_FIELDS
    ]
    for field in BOARD_SETTING_FIELDS:
        assert (
            "default" not in schema["properties"][field]
            and "anyOf" not in schema["properties"][field]
        )


@pytest.mark.parametrize(
    "changes",
    [
        {},
        *[{field: None} for field in BOARD_SETTING_FIELDS],
        {"name": " "},
        {"name": "a" * 81},
        {"description": "a" * 2001},
        {"rules": "a" * 10001},
        {"interest_ids": ["ai", "ai"]},
        {"interest_ids": ["a", "b", "c", "d"]},
        {"interest_ids": ["a" * 41]},
        {"interest_ids": [""]},
        {"status": "suspended"},
        {"join_policy": "approval"},
        {"visibility": "hidden"},
        {"slug": "new-slug"},
        {"owner_id": 2},
        {"avatar_asset_id": "00000000-0000-0000-0000-000000000002"},
        {"reason": " ", "name": "보드"},
        {"expected_revision": -1, "name": "보드"},
    ],
)
def test_invalid_settings_do_not_reach_service(settings_api, changes):
    client, service = settings_api
    response = client.patch(PATH, json={"expected_revision": 0, "reason": "설정", **changes})
    assert response.status_code == 422, response.text
    service.update.assert_not_awaited()
