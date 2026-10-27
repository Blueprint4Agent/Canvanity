from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import Board, BoardMember, BoardMemberAudit, BoardMemberGrade
from app.services.board_permission import BoardPermissionService
from tests.integration.api.v1.board.test_board_creation import PAYLOAD, signup

pytestmark = pytest.mark.primary_data


def test_join_leave_default_grade_idempotency_and_owner_guard(integration_client):
    client = integration_client
    owner, _ = signup(client, "join-owner")
    member, member_id = signup(client, "join-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    path = f"/api/v1/boards/{board['id']}"
    assert client.post(path + "/join").status_code == 401
    assert client.delete(path + "/membership").status_code == 401
    denied = client.delete(path + "/membership", headers=owner)
    assert denied.status_code == 409
    assert denied.json()["detail"]["error"] == "BOARD_OWNER_CANNOT_LEAVE"
    joined = client.post(path + "/join", headers=member)
    assert joined.status_code == 200
    assert joined.headers["cache-control"] == "private, no-store"
    assert joined.json()["role"] == "member" and joined.json()["grade_name"] == "뉴커머"
    assert client.post(path + "/join", headers=member).json() == joined.json()
    home = client.get(path + "/home", headers=member).json()
    assert home["board"]["revision"] == 1
    assert not home["shelves"][1]["capabilities"]["create_canvas"]
    assert home["shelves"][1]["capabilities"]["create_comment"]
    assert client.delete(path + "/membership", headers=member).status_code == 204
    assert client.delete(path + "/membership", headers=member).status_code == 204
    home = client.get(path + "/home", headers=member).json()
    assert home["membership"] is None and home["board"]["revision"] == 2
    assert not home["shelves"][1]["capabilities"]["create_comment"]

    async def check():
        async with get_db() as db:
            assert await db.get(BoardMember, (UUID(board["id"]), member_id)) is None
            actions = (
                await db.scalars(
                    select(BoardMemberAudit.action).where(
                        BoardMemberAudit.target_user_id == member_id
                    )
                )
            ).all()
            assert sorted(actions) == ["member_joined", "member_left"]

    client.portal.call(check)


@pytest.mark.parametrize("state", ["banned", "suspended", "pending"])
def test_membership_actions_do_not_clear_restrictions(integration_client, state):
    client = integration_client
    owner, _ = signup(client, "blocked-owner")
    member, member_id = signup(client, "blocked-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    path = f"/api/v1/boards/{board['id']}"
    assert client.post(path + "/join", headers=member).status_code == 200

    async def restrict():
        async with get_db() as db:
            row = await db.get(BoardMember, (UUID(board["id"]), member_id))
            row.status = state
            await db.commit()

    client.portal.call(restrict)
    assert client.post(path + "/join", headers=member).status_code == 403
    assert client.delete(path + "/membership", headers=member).status_code == (
        403 if state == "pending" else 404
    )

    async def check():
        async with get_db() as db:
            assert (await db.get(BoardMember, (UUID(board["id"]), member_id))).status == state

    client.portal.call(check)


def test_join_uses_current_default_and_rejects_private_archived_suspended(integration_client):
    client = integration_client
    owner, _ = signup(client, "current-owner")
    member, _ = signup(client, "current-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    path = f"/api/v1/boards/{board['id']}"

    async def change_default():
        async with get_db() as db:
            grades = (
                await db.scalars(
                    select(BoardMemberGrade)
                    .where(BoardMemberGrade.board_id == UUID(board["id"]))
                    .order_by(BoardMemberGrade.rank)
                )
            ).all()
            grades[0].is_default = False
            await db.flush()
            grades[1].is_default = True
            grades[1].name = "단골"
            await db.commit()

    client.portal.call(change_default)
    assert client.post(path + "/join", headers=member).json()["grade_name"] == "단골"
    assert client.delete(path + "/membership", headers=member).status_code == 204

    async def set_state(state):
        async with get_db() as db:
            row = await db.get(Board, UUID(board["id"]))
            row.status = state
            await db.commit()

    client.portal.call(set_state, "archived")
    assert client.post(path + "/join", headers=member).status_code == 403
    client.portal.call(set_state, "suspended")
    assert client.post(path + "/join", headers=member).status_code == 404
    assert client.delete(path + "/membership", headers=member).status_code == 404
    private = client.post(
        "/api/v1/boards",
        headers=owner,
        json={**PAYLOAD, "slug": "invite-only", "visibility": "private", "join_policy": "invite"},
    ).json()
    assert client.post(f"/api/v1/boards/{private['id']}/join", headers=member).status_code == 403


def test_join_rollback_and_injected_policy(integration_client):
    client = integration_client
    owner, _ = signup(client, "rollback-join-owner")
    member, member_id = signup(client, "rollback-join-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    path = f"/api/v1/boards/{board['id']}"
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("fail")):
        assert client.post(path + "/join", headers=member).status_code == 503

    async def check():
        async with get_db() as db:
            assert await db.get(BoardMember, (UUID(board["id"]), member_id)) is None
            assert (await db.get(Board, UUID(board["id"]))).revision == 0
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(BoardMemberAudit)
                    .where(BoardMemberAudit.target_user_id == member_id)
                )
                == 0
            )

    client.portal.call(check)

    class Deny(BoardPermissionService):
        @staticmethod
        def check_read(board, member):
            raise BoardException(BoardErrorCode.NOT_FOUND)

    client.app.dependency_overrides[BoardPermissionService] = Deny
    try:
        assert client.get(path + "/home", headers=owner).status_code == 404
        assert client.post(path + "/join", headers=member).status_code == 404
    finally:
        client.app.dependency_overrides.pop(BoardPermissionService)


def test_global_admin_and_other_board_owner_do_not_gain_board_staff(integration_client):
    from app.models.user import User

    client = integration_client
    owner, _ = signup(client, "scope-owner")
    outsider, outsider_id = signup(client, "scope-admin")
    public = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    private = client.post(
        "/api/v1/boards",
        json={**PAYLOAD, "slug": "scope-private", "visibility": "private", "join_policy": "invite"},
        headers=owner,
    ).json()

    async def promote_account():
        async with get_db() as db:
            (await db.get(User, outsider_id)).role = "admin"
            await db.commit()

    client.portal.call(promote_account)
    assert (
        client.post(
            "/api/v1/boards", json={**PAYLOAD, "slug": "outsider-owned"}, headers=outsider
        ).status_code
        == 201
    )
    path = f"/api/v1/boards/{public['id']}"
    joined = client.post(
        path + "/join", headers=outsider, json={"role": "owner", "status": "active"}
    )
    assert joined.status_code == 200
    assert joined.json()["role"] == "member" and joined.json()["grade_name"] == "뉴커머"
    home = client.get(path + "/home", headers=outsider).json()
    assert not home["shelves"][0]["capabilities"]["create_canvas"]
    assert not home["shelves"][1]["capabilities"]["create_canvas"]
    assert client.get(f"/api/v1/boards/{private['id']}/home", headers=outsider).status_code == 404
    assert client.post(f"/api/v1/boards/{private['id']}/join", headers=outsider).status_code == 403


def test_failed_leave_preserves_membership_audit_and_revision(integration_client):
    client = integration_client
    owner, _ = signup(client, "leave-rollback-owner")
    member, member_id = signup(client, "leave-rollback-member")
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=owner).json()
    path = f"/api/v1/boards/{board['id']}"
    assert client.post(path + "/join", headers=member).status_code == 200
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("fail")):
        assert client.delete(path + "/membership", headers=member).status_code == 503

    async def check():
        async with get_db() as db:
            assert (await db.get(BoardMember, (UUID(board["id"]), member_id))).status == "active"
            assert (await db.get(Board, UUID(board["id"]))).revision == 1
            assert list(
                (
                    await db.scalars(
                        select(BoardMemberAudit.action).where(
                            BoardMemberAudit.target_user_id == member_id
                        )
                    )
                ).all()
            ) == ["member_joined"]

    client.portal.call(check)
    assert client.delete(path + "/membership", headers=member).status_code == 204
