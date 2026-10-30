from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import Board, BoardMember
from app.models.user import User
from tests.integration.api.v1.board.test_board_member_administration import (
    roster as roster,
    snapshot,
    window,
)

pytestmark = pytest.mark.primary_data


@pytest.fixture
def invite_board(roster):
    r = roster

    async def configure():
        async with get_db() as db:
            board = await db.get(Board, UUID(r.board["id"]))
            board.visibility, board.join_policy = "private", "invite"
            await db.commit()

    r.client.portal.call(configure)
    return r


def revision(r):
    return r.client.get(r.path + "/home", headers=r.headers["owner"]).json()["board"]["revision"]


def invite(r, actor="owner", target="outsider", **changes):
    return r.client.post(
        r.path + "/members",
        headers=r.headers[actor],
        json={
            "user_id": r.ids[target],
            "expected_revision": revision(r),
            "reason": "운영자 수동 초대",
            **changes,
        },
    )


@pytest.mark.parametrize("actor", ["owner", "admin"])
def test_invitation_uses_current_default_grade_and_records_operator(invite_board, actor):
    r = invite_board
    assert r.client.get(r.path + "/home", headers=r.headers["outsider"]).status_code == 404
    changed = r.client.patch(
        r.path + f"/grades/{r.grades[2]['id']}",
        headers=r.headers["owner"],
        json={
            "expected_revision": revision(r),
            "reason": "현재 가입 기본값",
            "is_default": True,
        },
    )
    assert changed.status_code == 200
    before = revision(r)
    response = invite(r, actor)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["board_revision"] == before + 1
    assert body["member"]["role"] == "member" and body["member"]["status"] == "active"
    assert body["member"]["grade_id"] == r.grades[2]["id"]
    assert body["member"]["grade_name"] == "큐레이터"
    assert "email" not in body["member"] and "password" not in body["member"]
    assert response.headers["cache-control"] == "private, no-store"
    home = r.client.get(r.path + "/home", headers=r.headers["outsider"])
    assert home.status_code == 200 and home.json()["membership"]["role"] == "member"
    assert r.client.get(r.path + "/members", headers=r.headers["outsider"]).status_code == 403
    audits = r.client.get(
        r.path + "/member-audit", headers=r.headers["owner"], params=window()
    ).json()["items"]
    record = next(a for a in audits if a["action"] == "member_invited")
    assert record["actor_user_id"] == r.ids[actor] and record["target_user_id"] == r.ids["outsider"]
    assert record["before"] is None and record["after"] == {
        "role": "member",
        "status": "active",
        "grade_id": r.grades[2]["id"],
    }
    assert record["reason"] == "운영자 수동 초대"


@pytest.mark.parametrize("actor,expected", [("moderator", 403), ("member", 403), ("outsider", 404)])
def test_invitation_rejects_unauthorized_roles_without_writes(invite_board, actor, expected):
    r = invite_board
    before = snapshot(r)
    rejected = invite(r, actor)
    assert rejected.status_code == expected
    assert snapshot(r) == before


@pytest.mark.parametrize(
    "state,expected",
    [
        ("pending", 404),
        ("suspended", 404),
        ("banned", 404),
        ("archived", 403),
        ("board_suspended", 404),
    ],
)
def test_invitation_rechecks_current_actor_and_board_status(invite_board, state, expected):
    r = invite_board

    async def revoke():
        async with get_db() as db:
            if state in {"archived", "board_suspended"}:
                (await db.get(Board, UUID(r.board["id"]))).status = (
                    "suspended" if state == "board_suspended" else state
                )
            else:
                (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["admin"]))).status = state
            await db.commit()

    r.client.portal.call(revoke)
    before = snapshot(r)
    # Preserve the saved revision when the Board itself is hidden.
    response = r.client.post(
        r.path + "/members",
        headers=r.headers["admin"],
        json={
            "user_id": r.ids["outsider"],
            "expected_revision": before[0],
            "reason": "현재 권한 확인",
        },
    )
    assert response.status_code == expected
    assert snapshot(r) == before


def test_public_invite_policy_is_supported_and_open_registration_is_rejected(invite_board):
    r = invite_board

    async def configure(policy):
        async with get_db() as db:
            board = await db.get(Board, UUID(r.board["id"]))
            board.visibility, board.join_policy = "public", policy
            await db.commit()

    r.client.portal.call(configure, "open")
    before = snapshot(r)
    assert invite(r).status_code == 403
    assert snapshot(r) == before
    r.client.portal.call(configure, "invite")
    assert invite(r).status_code == 200


def test_active_members_preserve_role_grade_status_and_join_time_on_repeat(invite_board):
    r = invite_board
    changed = r.client.patch(
        r.path + f"/members/{r.ids['moderator']}",
        headers=r.headers["owner"],
        json={
            "expected_revision": revision(r),
            "reason": "등급 지정",
            "grade_id": r.grades[1]["id"],
        },
    )
    assert changed.status_code == 200
    before = snapshot(r)
    response = invite(r, "admin", "moderator")
    assert response.status_code == 200
    assert response.json() == changed.json()
    assert invite(r, "owner", "owner").json()["member"]["role"] == "owner"
    assert invite(r, "admin", "admin").json()["member"]["role"] == "admin"
    assert snapshot(r) == before
    stale = invite(r, expected_revision=0)
    assert stale.status_code == 409
    assert stale.json()["detail"]["details"]["current_revision"] == before[0]
    assert snapshot(r) == before


@pytest.mark.parametrize("state", ["pending", "suspended", "banned"])
def test_invitation_cannot_reset_existing_membership_status(invite_board, state):
    r = invite_board

    async def block():
        async with get_db() as db:
            (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["peer"]))).status = state
            await db.commit()

    r.client.portal.call(block)
    before = snapshot(r)
    response = invite(r, target="peer")
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "BOARD_INVITATION_CONFLICT"
    assert snapshot(r) == before


@pytest.mark.parametrize("missing", [False, True])
def test_only_existing_active_accounts_can_be_invited(invite_board, missing):
    r = invite_board
    if not missing:

        async def deactivate():
            async with get_db() as db:
                (await db.get(User, r.ids["outsider"])).is_active = False
                await db.commit()

        r.client.portal.call(deactivate)
    before = snapshot(r)
    response = invite(r, user_id=2**31 - 1 if missing else r.ids["outsider"])
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "BOARD_INVITEE_NOT_FOUND"
    assert snapshot(r) == before


def test_invitation_commit_failure_rolls_back_membership_revision_and_audit(invite_board):
    r = invite_board
    before = snapshot(r)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        response = invite(r)
    assert response.status_code == 503
    assert snapshot(r) == before
