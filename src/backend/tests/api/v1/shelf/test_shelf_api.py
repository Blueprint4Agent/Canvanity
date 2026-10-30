from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.board import (
    ACTIONS,
    BoardPoliciesResponse,
    ShelfPoliciesResponse,
    ShelfResponse,
    ShelvesResponse,
)
from app.routers.v1.shelf import router
from app.services.shelf import ShelfService

pytestmark = pytest.mark.api_test
BOARD = "00000000-0000-0000-0000-000000000001"
SHELF = "00000000-0000-0000-0000-000000000002"
GRADE = "00000000-0000-0000-0000-000000000003"
BASE = f"/api/v1/boards/{BOARD}"
PATH = f"/api/v1/shelves/{SHELF}"
MEMBER = {"audience": "members", "min_grade_id": GRADE, "staff_only": False, "staff_bypass": True}
POLICIES = {action: MEMBER for action in ACTIONS}
DATA = {
    "id": SHELF,
    "board_id": BOARD,
    "slug": "projects",
    "name": "프로젝트",
    "description": "",
    "icon": "blocks",
    "purpose": "general",
    "classification": "manual",
    "sort_order": 2,
    "is_default": False,
    "is_visible": True,
    "capabilities": {action: True for action in ACTIONS},
}


@pytest.fixture
def shelf_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    app.dependency_overrides[get_current_token_user] = lambda: None
    service = AsyncMock(spec=ShelfService)
    app.dependency_overrides[ShelfService] = lambda: service
    return TestClient(app), service


OPERATIONS = [
    ("GET", BASE + "/shelves", None, "list", 200),
    ("GET", PATH, None, "get", 200),
    ("POST", BASE + "/shelves", {"name": "프로젝트", "slug": "projects"}, "create", 201),
    ("PATCH", PATH, {"name": "새 분류"}, "change", 200),
    ("DELETE", PATH, {}, "delete", 204),
    ("PATCH", BASE + "/shelves/order", {"shelf_ids": [SHELF]}, "reorder", 200),
    ("GET", BASE + "/policies", None, "board_policies", 200),
    ("PUT", BASE + "/policies", {"actions": POLICIES}, "set_board_policies", 200),
    ("GET", PATH + "/policies", None, "shelf_policies", 200),
    (
        "PUT",
        PATH + "/policies",
        {"actions": {action: None for action in ACTIONS}},
        "set_shelf_policies",
        200,
    ),
]


@pytest.mark.parametrize("method,path,body,operation,status", OPERATIONS)
def test_shelf_router_success_contract(shelf_api, method, path, body, operation, status):
    client, service = shelf_api
    if operation in {"list", "reorder"}:
        result = ShelvesResponse(items=[DATA], board_revision=4)
    elif "board_policies" in operation:
        result = BoardPoliciesResponse(board_id=BOARD, actions=POLICIES, board_revision=4)
    elif "shelf_policies" in operation:
        result = ShelfPoliciesResponse(
            board_id=BOARD,
            shelf_id=SHELF,
            actions={action: None for action in ACTIONS},
            effective_actions=POLICIES,
            board_revision=4,
        )
    elif operation == "delete":
        result = 4
    else:
        result = ShelfResponse(shelf=DATA, board_revision=4)
    getattr(service, operation).return_value = result
    payload = {"expected_revision": 3, "reason": "분류 설정", **body} if body is not None else None
    response = client.request(method, path, json=payload)
    assert response.status_code == status, response.text
    assert response.headers["cache-control"] == "private, no-store"
    if status == 204:
        assert response.content == b"" and response.headers["x-board-revision"] == "4"
    else:
        assert response.json() == result.model_dump(mode="json")
    if status == 201:
        assert response.headers["location"] == PATH
    getattr(service, operation).assert_awaited_once()


@pytest.mark.parametrize(
    "method,path,body,operation,status", [o for o in OPERATIONS if o[3] not in {"list", "get"}]
)
def test_shelf_management_requires_session(shelf_api, method, path, body, operation, status):
    client, service = shelf_api
    client.app.dependency_overrides.pop(get_current_session_user)
    payload = {"expected_revision": 3, "reason": "설정", **body} if body is not None else None
    assert client.request(method, path, json=payload).status_code == 401
    getattr(service, operation).assert_not_awaited()


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"name": None},
        {"name": " "},
        {"name": "a" * 81},
        {"slug": "UPPER"},
        {"slug": "a"},
        {"slug": "bad--slug"},
        {"description": None},
        {"description": "a" * 2001},
        {"icon": ""},
        {"classification": "smart"},
        {"purpose": "smart"},
        {"is_visible": "false"},
        {"is_visible": None},
        {"is_default": True},
        {"board_id": BOARD},
        {"sort_order": 1},
        {"name": "통과", "reason": " "},
    ],
)
def test_shelf_patch_rejects_invalid_fields_before_service(shelf_api, fields):
    client, service = shelf_api
    assert (
        client.patch(PATH, json={"expected_revision": 3, "reason": "설정", **fields}).status_code
        == 422
    )
    service.change.assert_not_awaited()


@pytest.mark.parametrize(
    "actions",
    [
        {},
        {**POLICIES, "react": None},
        {**POLICIES, "unknown": MEMBER},
        {**POLICIES, "react": {"audience": "public"}},
        {**POLICIES, "react": {"audience": "members"}},
        {**POLICIES, "read_canvas": {"audience": "public", "min_grade_id": GRADE}},
        {**POLICIES, "react": {**MEMBER, "staff_only": True}},
        {**POLICIES, "react": {**MEMBER, "staff_bypass": "false"}},
    ],
)
def test_policy_shape_and_complete_replacement_are_required(shelf_api, actions):
    client, service = shelf_api
    response = client.put(
        BASE + "/policies", json={"expected_revision": 3, "reason": "정책", "actions": actions}
    )
    assert response.status_code == 422, response.text
    service.set_board_policies.assert_not_awaited()


def test_shelf_order_rejects_duplicate_and_oversized_ids(shelf_api):
    client, service = shelf_api
    for ids in ([], [SHELF, SHELF], [str(UUID(int=i + 1)) for i in range(101)]):
        assert (
            client.patch(
                BASE + "/shelves/order",
                json={"expected_revision": 3, "reason": "순서", "shelf_ids": ids},
            ).status_code
            == 422
        )
    service.reorder.assert_not_awaited()
