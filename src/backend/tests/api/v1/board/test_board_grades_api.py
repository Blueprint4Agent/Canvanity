from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error.board_exception import BoardErrorCode, BoardException
from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.board import BoardGradePatchForm, BoardGradeResponse, BoardGradesResponse
from app.routers.v1.board import router
from app.services.board_grade import BoardGradeService

pytestmark = pytest.mark.api_test
BOARD = UUID("00000000-0000-0000-0000-000000000001")
GRADE = "00000000-0000-0000-0000-000000000002"
PATH = f"/api/v1/boards/{BOARD}/grades"
GRADE_DATA = {"id": GRADE, "name": "뉴커머", "rank": 0, "is_default": True}


@pytest.fixture
def grade_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/boards")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    app.dependency_overrides[get_current_token_user] = lambda: None
    service = AsyncMock(spec=BoardGradeService)
    app.dependency_overrides[BoardGradeService] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize(
    "method,suffix,body,operation,expected",
    [
        ("GET", "", None, "list", 200),
        ("POST", "", {"name": "뉴커머", "rank": 0}, "create", 201),
        ("PATCH", "/order", {"grade_ids": [GRADE]}, "reorder", 200),
        ("PATCH", f"/{GRADE}", {"is_default": True}, "change", 200),
        ("DELETE", f"/{GRADE}", {"replacement_grade_id": GRADE}, "delete", 200),
    ],
)
def test_grade_router_contract(grade_api, method, suffix, body, operation, expected):
    client, service = grade_api
    data = {"board_revision": 4}
    data["grade" if operation in {"create", "change"} else "items"] = (
        GRADE_DATA if operation in {"create", "change"} else [GRADE_DATA]
    )
    getattr(service, operation).return_value = (
        BoardGradeResponse(**data)
        if operation in {"create", "change"}
        else BoardGradesResponse(**data)
    )
    payload = {"expected_revision": 3, "reason": "등급 설정", **body} if body else None
    response = client.request(method, PATH + suffix, json=payload)
    assert response.status_code == expected, response.text
    assert response.json() == data
    assert response.headers["cache-control"] == "private, no-store"
    if expected == 201:
        assert response.headers["location"] == PATH + f"/{GRADE}"
    getattr(service, operation).assert_awaited_once()


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"name": None},
        {"is_default": None},
        {"is_default": False},
        {"name": "  "},
        {"name": "a" * 31},
        {"rank": 30},
        {"owner_id": 1},
        {"name": "Valid", "reason": " "},
    ],
)
def test_grade_patch_rejects_invalid_input_before_service(grade_api, changes):
    client, service = grade_api
    response = client.patch(
        PATH + f"/{GRADE}", json={"expected_revision": 3, "reason": "설정", **changes}
    )
    assert response.status_code == 422
    service.change.assert_not_awaited()


@pytest.mark.parametrize("rank", [-1, 2**31, 1.5, True])
def test_grade_rank_respects_database_integer_range(grade_api, rank):
    client, service = grade_api
    response = client.post(
        PATH, json={"expected_revision": 3, "reason": "추가", "name": "새 등급", "rank": rank}
    )
    assert response.status_code == 422
    service.create.assert_not_awaited()


def test_grade_patch_schema_and_error_message_follow_contract(grade_api):
    schema = BoardGradePatchForm.model_json_schema()
    assert schema["required"] == ["expected_revision", "reason"]
    assert [v["required"] for v in schema["allOf"][0]["anyOf"]] == [["name"], ["is_default"]]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["is_default"]["const"] is True
    assert all("default" not in schema["properties"][field] for field in ("name", "is_default"))
    client, service = grade_api
    service.list.side_effect = BoardException(BoardErrorCode.NOT_FOUND)
    response = client.get(PATH, headers={"Accept-Language": "ko"})
    assert response.status_code == 404
    assert response.json()["detail"] == {"error": "BOARD_NOT_FOUND", "message": "Board not found."}
