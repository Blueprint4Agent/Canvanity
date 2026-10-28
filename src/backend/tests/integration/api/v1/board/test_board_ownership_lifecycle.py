from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.core.error import AuthErrorCode, AuthException
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
from tests.integration.api.v1.auth.test_profile_photo import png
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import (
    roster as roster,
    snapshot,
    window,
)

pytestmark = pytest.mark.primary_data
CHILDREN = (
    BoardInterest,
    BoardLayout,
    BoardMember,
    BoardMemberAudit,
    BoardMemberGrade,
    BoardPolicy,
    Shelf,
    ShelfPolicy,
)


def revision(r):
    return snapshot(r)[0]


def transfer(r, actor="owner", target="member", **changes):
    return r.client.post(
        r.path + "/ownership-transfer",
        headers=r.headers[actor],
        json={
            "expected_revision": revision(r),
            "target_user_id": r.ids[target],
            "reason": "운영 책임 위임",
            **changes,
        },
    )


def state(r):
    async def read():
        async with get_db() as db:
            board = await db.get(Board, UUID(r.board["id"]))
            return (
                board.owner_id,
                board.status,
                [
                    await db.scalar(
                        select(func.count()).select_from(model).where(model.board_id == board.id)
                    )
                    for model in CHILDREN
                ],
            )

    return r.client.portal.call(read), snapshot(r)


def archive(r):
    response = r.client.patch(
        r.path,
        headers=r.headers["owner"],
        json={
            "expected_revision": revision(r),
            "reason": "커뮤니티 종료 준비",
            "status": "archived",
        },
    )
    assert response.status_code == 200, response.text


def delete(r, actor="owner", **changes):
    return r.client.request(
        "DELETE",
        r.path,
        headers=r.headers[actor],
        json={"expected_revision": revision(r), "confirm_slug": r.board["slug"], **changes},
    )


@pytest.mark.parametrize("target", ["member", "admin", "moderator"])
def test_transfer_keeps_activity_and_immediately_changes_owner_permissions(roster, target):
    r = roster
    before = state(r)
    joined_before = {
        m["user_id"]: m["joined_at"]
        for m in r.client.get(r.path + "/members", headers=r.headers["owner"]).json()["items"]
    }
    response = transfer(r, target=target)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "board_id": r.board["id"],
        "previous_owner_id": r.ids["owner"],
        "owner_id": r.ids[target],
        "board_revision": before[1][0] + 1,
    }
    after = state(r)
    assert {
        m["user_id"]: m["joined_at"]
        for m in r.client.get(r.path + "/members", headers=r.headers["owner"]).json()["items"]
    } == joined_before
    assert after[0][0] == r.ids[target]
    before_members = {m[0]: m for m in before[1][1]}
    after_members = {m[0]: m for m in after[1][1]}
    assert (
        after_members[r.ids["owner"]][1] == "admin" and after_members[r.ids[target]][1] == "owner"
    )
    assert sum(m[1] == "owner" for m in after[1][1]) == 1
    assert all(before_members[user][2:] == member[2:] for user, member in after_members.items())
    assert transfer(r, target="peer").status_code == 403
    assert delete(r).status_code == 403
    owner_only = {
        "expected_revision": revision(r),
        "reason": "공개 범위 관리",
        "visibility": "private",
        "join_policy": "invite",
    }
    assert r.client.patch(r.path, headers=r.headers["owner"], json=owner_only).status_code == 403
    assert r.client.patch(r.path, headers=r.headers[target], json=owner_only).status_code == 200
    audits = r.client.get(
        r.path + "/member-audit", headers=r.headers[target], params=window()
    ).json()["items"]
    audit = next(a for a in audits if a["action"] == "ownership_transferred")
    assert audit["actor_user_id"] == r.ids["owner"] and audit["target_user_id"] == r.ids[target]
    assert audit["before"] is None and audit["after"] is None
    assert audit["ownership_change"]["before"]["owner_id"] == r.ids["owner"]
    assert audit["ownership_change"]["after"]["owner_id"] == r.ids[target]
    assert all(
        set(m) == {"user_id", "role", "status", "grade_id"}
        for m in audit["ownership_change"]["after"]["members"]
    )


@pytest.mark.parametrize("actor", ["admin", "moderator", "member", "outsider"])
def test_only_current_owner_can_transfer(roster, actor):
    r = roster
    before = state(r)
    assert transfer(r, actor).status_code == 403
    assert state(r) == before


@pytest.mark.parametrize(
    "target,status",
    [
        ("owner", None),
        ("outsider", None),
        ("member", "pending"),
        ("member", "suspended"),
        ("member", "banned"),
        ("member", "inactive_account"),
    ],
)
def test_transfer_rejects_invalid_successor_without_changes(roster, target, status):
    r = roster

    async def configure():
        async with get_db() as db:
            if status == "inactive_account":
                (await db.get(User, r.ids[target])).is_active = False
            elif status:
                (await db.get(BoardMember, (UUID(r.board["id"]), r.ids[target]))).status = status
            await db.commit()

    r.client.portal.call(configure)
    before = state(r)
    response = transfer(r, target=target)
    assert (
        response.status_code == 422
        and response.json()["detail"]["error"] == "BOARD_INVALID_OWNERSHIP_TARGET"
    )
    assert state(r) == before


def test_transfer_archive_stale_and_rollback_boundaries(roster):
    r = roster
    archive(r)
    before = state(r)
    assert transfer(r, expected_revision=0).status_code == 409
    assert state(r) == before
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        assert transfer(r).status_code == 503
    assert state(r) == before
    assert transfer(r).status_code == 200
    assert state(r)[0][1] == "archived"


def test_suspended_board_cannot_transfer_or_delete(roster):
    r = roster

    async def suspend():
        async with get_db() as db:
            (await db.get(Board, UUID(r.board["id"]))).status = "suspended"
            await db.commit()

    r.client.portal.call(suspend)
    before = state(r)
    assert transfer(r).status_code == 404 and delete(r).status_code == 404
    assert state(r) == before


def test_transfer_unblocks_former_owner_account_deletion_and_protects_successor(roster):
    r = roster
    old_email = r.client.get("/api/v1/auth/me", headers=r.headers["owner"]).json()["email"]
    new_email = r.client.get("/api/v1/auth/me", headers=r.headers["member"]).json()["email"]
    assert transfer(r).status_code == 200

    async def delete_accounts():
        with pytest.raises(AuthException) as protected:
            await Users.delete_account(r.ids["member"], new_email)
        assert protected.value.code.error == AuthErrorCode.BOARD_OWNERSHIP_REQUIRED.code.error
        await Users.delete_account(r.ids["owner"], old_email)
        async with get_db() as db:
            assert await db.get(User, r.ids["owner"]) is None
            assert (await db.get(Board, UUID(r.board["id"]))).owner_id == r.ids["member"]
            assert (
                await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))
            ).role == "owner"

    r.client.portal.call(delete_accounts)


def test_archived_delete_clears_board_data_and_preserves_users_other_board_and_photo(roster):
    r = roster
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "preserved-board"}
    ).json()
    upload = r.client.put(
        "/api/v1/auth/me/photo",
        content=png(),
        headers={**r.headers["owner"], "Content-Type": "image/png"},
    )
    assert upload.status_code == 200
    photo_url = upload.json()["profile_image_url"]
    photo = r.client.get(photo_url, headers=r.headers["owner"])
    assert photo.status_code == 200
    assert delete(r).status_code == 409
    archive(r)
    before = state(r)
    assert delete(r, confirm_slug="wrong-confirmation").status_code == 422
    assert delete(r, expected_revision=0).status_code == 409
    assert state(r) == before
    assert delete(r).status_code == 204
    assert r.client.get(r.path).status_code == 404

    async def inspect():
        async with get_db() as db:
            assert await db.get(Board, UUID(r.board["id"])) is None
            counts = [
                await db.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.board_id == UUID(r.board["id"]))
                )
                for model in CHILDREN
            ]
            assert all(count == 0 for count in counts)
            assert await db.get(Board, UUID(other["id"])) is not None
            assert await db.scalar(select(func.count()).select_from(User)) == 6

    r.client.portal.call(inspect)
    preserved = r.client.get(photo_url, headers=r.headers["owner"])
    assert preserved.status_code == 200 and preserved.content == photo.content


@pytest.mark.parametrize("actor", ["admin", "moderator", "member", "outsider"])
def test_archived_delete_requires_owner(roster, actor):
    r = roster
    archive(r)
    before = state(r)
    assert delete(r, actor).status_code == 403
    assert state(r) == before


def test_archived_delete_commit_failure_restores_every_child(roster):
    r = roster
    archive(r)
    before = state(r)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        assert delete(r).status_code == 503
    assert state(r) == before
