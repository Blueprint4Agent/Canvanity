import asyncio
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import (
    Board,
    BoardInterest,
    BoardLayout,
    BoardMember,
    BoardMemberAudit,
    BoardMemberGrade,
    BoardPolicy,
    Shelf,
    ShelfPolicy,
)
from app.models.user import User, Users
from app.services.board import BoardService
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


def signup(client, suffix):
    email = f"board-{suffix}@example.com"
    response = client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
    assert response.status_code == 200
    login = client.post("/api/v1/auth/login", json=build_login_payload(email=email)).json()
    return {"Authorization": f"Bearer {login['access_token']}"}, login["user"]["id"]


PAYLOAD = {
    "name": "에이전트 연구소",
    "slug": "agent-lab",
    "description": "설계와 경험을 나눕니다.",
    "interest_ids": ["ai", "development"],
}


def test_creation_initializes_aggregate_and_private_visibility(integration_client):
    client = integration_client
    headers, user_id = signup(client, "owner")
    outsider, _ = signup(client, "outsider")
    response = client.post("/api/v1/boards", json=PAYLOAD, headers=headers)
    assert response.status_code == 201, response.text
    board = response.json()
    assert response.headers["location"] == f"/api/v1/boards/{board['id']}"
    assert board["owner_id"] == user_id
    assert board["interest_ids"] == ["ai", "development"]
    home = client.get("/api/v1/boards/by-slug/agent-lab", headers=headers)
    assert home.status_code == 200
    data = home.json()
    assert data["membership"]["role"] == "owner"
    assert data["membership"]["grade_name"] == "뉴커머"
    assert [(g["name"], g["rank"]) for g in data["grades"]] == [
        ("뉴커머", 0),
        ("피너", 10),
        ("큐레이터", 20),
    ]
    assert [s["slug"] for s in data["shelves"]] == ["notice", "general"]
    assert all(s["capabilities"]["create_canvas"] for s in data["shelves"])
    assert data["layout"]["schema_version"] == 1 and len(data["layout"]["widgets"]) == 3
    public = client.get(f"/api/v1/boards/{board['id']}/home")
    assert public.status_code == 200 and public.json()["membership"] is None
    assert not any(s["capabilities"]["create_canvas"] for s in public.json()["shelves"])
    private = client.post(
        "/api/v1/boards",
        headers=headers,
        json={**PAYLOAD, "slug": "private-lab", "visibility": "private", "join_policy": "invite"},
    ).json()
    assert client.get(f"/api/v1/boards/{private['id']}/home", headers=headers).status_code == 200
    assert client.get("/api/v1/boards/by-slug/private-lab", headers=outsider).status_code == 404
    assert client.get(f"/api/v1/boards/{private['id']}/home").status_code == 404
    assert len(client.get("/api/v1/boards").json()["items"]) == 1
    assert len(client.get("/api/v1/boards", headers=headers).json()["items"]) == 2
    assert client.get("/api/v1/boards?mine=true").status_code == 401
    assert client.get("/api/v1/boards?mine=true", headers=outsider).json()["items"] == []
    assert home.headers["cache-control"] == "private, no-store"


def test_duplicate_invalid_catalog_and_failure_roll_back(integration_client):
    client = integration_client
    headers, _ = signup(client, "rollback")
    assert client.post("/api/v1/boards", json=PAYLOAD, headers=headers).status_code == 201
    duplicate = client.post("/api/v1/boards", json=PAYLOAD, headers=headers)
    assert (
        duplicate.status_code == 409 and duplicate.json()["detail"]["error"] == "BOARD_SLUG_TAKEN"
    )
    invalid = client.post(
        "/api/v1/boards",
        json={**PAYLOAD, "slug": "invalid-interest", "interest_ids": ["not-official"]},
        headers=headers,
    )
    assert invalid.status_code == 422

    async def failing_initializer(*args):
        raise SQLAlchemyError("controlled initialization failure")

    with patch.object(BoardService, "_initialize", failing_initializer):
        failed = client.post(
            "/api/v1/boards", json={**PAYLOAD, "slug": "rolled-back"}, headers=headers
        )
    assert failed.status_code == 503
    assert client.get("/api/v1/boards/by-slug/rolled-back", headers=headers).status_code == 404

    async def counts():
        async with get_db() as db:
            return [
                await db.scalar(select(func.count()).select_from(model))
                for model in (
                    Board,
                    BoardMember,
                    BoardMemberGrade,
                    Shelf,
                    BoardPolicy,
                    ShelfPolicy,
                    BoardLayout,
                    BoardMemberAudit,
                    BoardInterest,
                )
            ]

    assert asyncio.run(counts()) == [1, 1, 3, 2, 4, 2, 1, 1, 2]


def test_cursor_scope_and_current_member_restrictions(integration_client):
    client = integration_client
    headers, user_id = signup(client, "cursor")
    for slug in ["first-board", "second-board", "third-board"]:
        assert (
            client.post(
                "/api/v1/boards", json={**PAYLOAD, "slug": slug}, headers=headers
            ).status_code
            == 201
        )
    first = client.get("/api/v1/boards?limit=2").json()
    second = client.get(
        "/api/v1/boards", params={"limit": 2, "cursor": first["next_cursor"]}
    ).json()
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert not ({b["id"] for b in first["items"]} & {b["id"] for b in second["items"]})
    assert (
        client.get(
            "/api/v1/boards", params={"cursor": first["next_cursor"], "q": "other"}
        ).status_code
        == 422
    )
    assert client.get("/api/v1/boards?cursor=invalid").status_code == 422
    assert len(client.get("/api/v1/boards?interest_id=ai").json()["items"]) == 3
    assert client.get("/api/v1/boards?interest_id=not-official").json()["items"] == []
    board_id = UUID(first["items"][0]["id"])

    async def suspend():
        async with get_db() as db:
            member = await db.get(BoardMember, (board_id, user_id))
            member.status = "suspended"
            await db.commit()

    asyncio.run(suspend())
    assert client.get(f"/api/v1/boards/{board_id}/home", headers=headers).status_code == 404
    assert len(client.get("/api/v1/boards", headers=headers).json()["items"]) == 2


def test_owner_can_remove_empty_board_without_leaking_account_or_bypassing_confirmation(
    integration_client,
):
    client = integration_client
    headers, user_id = signup(client, "delete")
    outsider, _ = signup(client, "other-delete")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=headers).json()
    path = f"/api/v1/boards/{board['id']}"

    def remove(auth, **overrides):
        return client.request(
            "DELETE",
            path,
            headers=auth,
            json={"expected_revision": 0, "confirm_slug": board["slug"], **overrides},
        )

    assert remove(outsider).status_code == 403
    assert remove(headers, expected_revision=1).status_code == 409
    assert remove(headers, confirm_slug="incorrect").status_code == 422

    async def owner_delete_guard():
        async with get_db() as db:
            user = await db.get(User, user_id)
            email = user.email
        from app.core.error import AuthErrorCode, AuthException

        with pytest.raises(AuthException) as error:
            await Users.delete_account(user_id, email)
        assert error.value.code.error == AuthErrorCode.BOARD_OWNERSHIP_REQUIRED.code.error

    asyncio.run(owner_delete_guard())
    assert remove(headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404

    async def remaining():
        async with get_db() as db:
            assert await db.scalar(select(func.count()).select_from(BoardMemberGrade)) == 0
            assert await db.scalar(select(func.count()).select_from(BoardMemberAudit)) == 0

    asyncio.run(remaining())


def test_default_grade_does_not_grant_staff_permissions(integration_client):
    client = integration_client
    owner, _ = signup(client, "policy-owner")
    member_headers, member_id = signup(client, "policy-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    home = client.get(f"/api/v1/boards/{board['id']}/home", headers=owner).json()

    async def assign(index):
        async with get_db() as db:
            key = (UUID(board["id"]), member_id)
            member = await db.get(BoardMember, key)
            if member is None:
                db.add(
                    BoardMember(
                        board_id=key[0],
                        user_id=member_id,
                        grade_id=UUID(home["grades"][index]["id"]),
                        role="member",
                        status="active",
                    )
                )
            else:
                member.grade_id = UUID(home["grades"][index]["id"])
            await db.commit()

    asyncio.run(assign(0))
    newcomer = client.get(f"/api/v1/boards/{board['id']}/home", headers=member_headers).json()
    general = next(s for s in newcomer["shelves"] if s["slug"] == "general")
    assert (
        not general["capabilities"]["create_canvas"] and general["capabilities"]["create_comment"]
    )
    asyncio.run(assign(2))
    curator = client.get(f"/api/v1/boards/{board['id']}/home", headers=member_headers).json()
    assert next(s for s in curator["shelves"] if s["slug"] == "general")["capabilities"][
        "create_canvas"
    ]
    assert not next(s for s in curator["shelves"] if s["slug"] == "notice")["capabilities"][
        "create_canvas"
    ]
    assert curator["membership"]["role"] == "member"
    assert (
        client.request(
            "DELETE",
            f"/api/v1/boards/{board['id']}",
            headers=owner,
            json={"expected_revision": 0, "confirm_slug": board["slug"]},
        ).status_code
        == 409
    )
