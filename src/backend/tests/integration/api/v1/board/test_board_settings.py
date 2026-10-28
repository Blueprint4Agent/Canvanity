from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import Board, BoardInterest, BoardMember
from app.models.interest import Interest
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import (
    roster as roster,
    snapshot,
    window,
)

pytestmark = pytest.mark.primary_data


def current(r):
    response = r.client.get(r.path, headers=r.headers["owner"])
    assert response.status_code == 200, response.text
    return response.json()


def change(r, actor="owner", **changes):
    return r.client.patch(
        r.path,
        headers=r.headers[actor],
        json={
            "expected_revision": current(r)["board"]["revision"],
            "reason": "보드 운영 설정",
            **changes,
        },
    )


def settings_snapshot(r):
    async def read():
        async with get_db() as db:
            board = await db.get(Board, UUID(r.board["id"]))
            ids = list(
                (
                    await db.scalars(
                        select(Interest.slug)
                        .join(BoardInterest, BoardInterest.interest_id == Interest.id)
                        .where(BoardInterest.board_id == board.id)
                        .order_by(BoardInterest.position)
                    )
                ).all()
            )
            return (
                board.name,
                board.description,
                board.rules,
                board.visibility,
                board.join_policy,
                board.status,
            ), ids

    return r.client.portal.call(read), snapshot(r)


@pytest.mark.parametrize("actor", ["owner", "admin"])
def test_metadata_and_ordered_interests_update_with_allowlisted_audit(roster, actor):
    r = roster
    before = current(r)
    profile_interests = r.client.get("/api/v1/auth/me", headers=r.headers[actor]).json()[
        "interests"
    ]
    response = change(
        r,
        actor,
        name="  새 이름  ",
        description="소개",
        rules="# 운영 규칙\n서로 존중합니다.",
        interest_ids=["development", "ai"],
        join_policy="invite",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["board"]["name"] == "새 이름" and body["rules"].startswith("# 운영 규칙")
    assert body["board"]["interest_ids"] == ["development", "ai"]
    assert body["board_revision"] == before["board"]["revision"] + 1 == body["board"]["revision"]
    assert response.headers["cache-control"] == "private, no-store"
    home = current(r)
    assert home["grades"] == before["grades"] and home["layout"] == before["layout"]
    assert home["membership"] == before["membership"]
    assert (
        r.client.get("/api/v1/auth/me", headers=r.headers[actor]).json()["interests"]
        == profile_interests
    )
    assert r.client.post(r.path + "/join", headers=r.headers["outsider"]).status_code == 403
    audits = r.client.get(r.path + "/member-audit", headers=r.headers["owner"], params=window())
    assert audits.status_code == 200, audits.text
    audit = next(a for a in audits.json()["items"] if a["action"] == "board_updated")
    assert audit["actor_user_id"] == r.ids[actor] and audit["target_user_id"] is None
    assert audit["before"] is None and audit["after"] is None and audit["grade_change"] is None
    assert audit["board_change"]["before"]["name"] == before["board"]["name"]
    assert audit["board_change"]["after"]["interest_ids"] == ["development", "ai"]
    assert set(audit["board_change"]["after"]) == {
        "name",
        "description",
        "rules",
        "interest_ids",
        "visibility",
        "join_policy",
        "status",
    }
    saved = settings_snapshot(r)
    assert (
        change(
            r,
            actor,
            name="새 이름",
            description="소개",
            rules=body["rules"],
            interest_ids=["development", "ai"],
        ).status_code
        == 200
    )
    assert settings_snapshot(r) == saved
    stale = change(r, expected_revision=before["board"]["revision"], name="다른 이름")
    assert (
        stale.status_code == 409
        and stale.json()["detail"]["details"]["current_revision"] == body["board_revision"]
    )
    assert settings_snapshot(r) == saved


@pytest.mark.parametrize("actor", ["moderator", "member", "outsider"])
def test_settings_rejects_non_managers_and_other_board_owner(roster, actor):
    r = roster
    if actor == "outsider":
        assert (
            r.client.post(
                "/api/v1/boards",
                headers=r.headers[actor],
                json={**PAYLOAD, "slug": "foreign-owner"},
            ).status_code
            == 201
        )
    before = settings_snapshot(r)
    assert change(r, actor, name="불가").status_code == 403
    assert settings_snapshot(r) == before


def test_admin_cannot_include_privileged_fields_even_with_same_value(roster):
    r = roster
    before = settings_snapshot(r)
    for fields in (
        {"visibility": "public"},
        {"visibility": "private", "join_policy": "invite"},
        {"status": "active"},
        {"status": "archived"},
    ):
        assert change(r, "admin", name="부분 수정 불가", **fields).status_code == 403
        assert settings_snapshot(r) == before


@pytest.mark.parametrize("status,expected", [("pending", 403), ("suspended", 404), ("banned", 404)])
def test_settings_uses_current_actor_status(roster, status, expected):
    r = roster

    async def revoke():
        async with get_db() as db:
            (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["admin"]))).status = status
            await db.commit()

    r.client.portal.call(revoke)
    before = settings_snapshot(r)
    assert change(r, "admin", name="불가").status_code == expected
    assert settings_snapshot(r) == before


def test_visibility_changes_keep_members_and_policies_and_require_explicit_invite(roster):
    r = roster
    before = current(r)
    state = settings_snapshot(r)
    assert change(r, visibility="private").status_code == 422
    assert settings_snapshot(r) == state
    assert change(r, join_policy="invite").status_code == 200
    state = settings_snapshot(r)
    assert change(r, visibility="private").status_code == 422
    assert settings_snapshot(r) == state
    response = change(r, visibility="private", join_policy="invite")
    assert response.status_code == 200
    assert r.client.get(r.path).status_code == 404
    assert r.client.get(r.path, headers=r.headers["outsider"]).status_code == 404
    assert r.client.get("/api/v1/boards/by-slug/" + r.board["slug"]).status_code == 404
    assert r.board["id"] not in [b["id"] for b in r.client.get("/api/v1/boards").json()["items"]]
    member_home = r.client.get(r.path, headers=r.headers["member"])
    assert member_home.status_code == 200 and len(member_home.json()["shelves"]) == 2
    assert current(r)["layout"] == before["layout"] and current(r)["grades"] == before["grades"]
    assert snapshot(r)[1] == state[1][1]
    state = settings_snapshot(r)
    assert change(r, join_policy="open").status_code == 422
    assert settings_snapshot(r) == state
    assert change(r, visibility="public", join_policy="open").status_code == 200
    assert len(r.client.get(r.path).json()["shelves"]) == 2
    assert r.client.post(r.path + "/join", headers=r.headers["outsider"]).status_code == 200


def test_private_members_policy_does_not_become_public_on_visibility_change(roster):
    r = roster
    private = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={
            **PAYLOAD,
            "slug": "private-settings",
            "visibility": "private",
            "join_policy": "invite",
        },
    ).json()
    path = f"/api/v1/boards/{private['id']}"
    assert (
        r.client.patch(
            path,
            headers=r.headers["owner"],
            json={"expected_revision": 0, "reason": "공개 보드로 전환", "visibility": "public"},
        ).status_code
        == 200
    )
    anonymous = r.client.get(path)
    assert anonymous.status_code == 200 and anonymous.json()["shelves"] == []


def test_archive_is_read_only_until_owner_explicitly_restores(roster):
    r = roster
    before = current(r)
    archived = change(r, status="archived")
    assert archived.status_code == 200
    home = r.client.get(r.path, headers=r.headers["member"]).json()
    assert home["board"]["status"] == "archived"
    assert all(not shelf["capabilities"]["create_canvas"] for shelf in home["shelves"])
    assert home["layout"] == before["layout"]
    state = settings_snapshot(r)
    assert change(r, name="복원 없는 수정").status_code == 403
    assert change(r, "admin", status="active").status_code == 403
    assert r.client.post(r.path + "/join", headers=r.headers["outsider"]).status_code == 403
    assert change(r, status="archived").status_code == 200
    assert settings_snapshot(r) == state
    audits = r.client.get(r.path + "/member-audit", headers=r.headers["owner"], params=window())
    assert audits.status_code == 200
    assert (
        next(a for a in audits.json()["items"] if a["action"] == "board_updated")["board_change"][
            "after"
        ]["status"]
        == "archived"
    )
    restored = change(r, status="active", name="복원한 보드")
    assert restored.status_code == 200 and restored.json()["board"]["status"] == "active"


def test_suspended_board_cannot_be_changed_or_restored_here(roster):
    r = roster

    async def suspend():
        async with get_db() as db:
            (await db.get(Board, UUID(r.board["id"]))).status = "suspended"
            await db.commit()

    r.client.portal.call(suspend)
    state = settings_snapshot(r)
    response = r.client.patch(
        r.path,
        headers=r.headers["owner"],
        json={"expected_revision": state[1][0], "reason": "복원 시도", "status": "active"},
    )
    assert response.status_code == 404 and settings_snapshot(r) == state


def test_official_interests_active_validation_clear_and_board_isolation(roster):
    r = roster
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "other-settings"}
    ).json()
    other_path = f"/api/v1/boards/{other['id']}"
    original = r.client.get(other_path).json()["board"]["interest_ids"]
    before = settings_snapshot(r)
    rejected = change(r, name="부분 저장 불가", interest_ids=["free-tag"])
    assert (
        rejected.status_code == 422
        and rejected.json()["detail"]["error"] == "BOARD_INVALID_INTEREST"
    )
    assert settings_snapshot(r) == before

    async def deactivate():
        async with get_db() as db:
            (await db.scalar(select(Interest).where(Interest.slug == "development"))).active = False
            await db.commit()

    r.client.portal.call(deactivate)
    assert change(r, interest_ids=["development"]).status_code == 422
    assert settings_snapshot(r) == before
    preserved = change(r, name="기존 참조 보존")
    assert preserved.status_code == 200
    assert preserved.json()["board"]["interest_ids"] == current(r)["board"]["interest_ids"]
    assert change(r, interest_ids=[], description="", rules="").status_code == 200
    assert current(r)["board"]["interest_ids"] == []

    async def stored_other_interests():
        async with get_db() as db:
            return list(
                (
                    await db.scalars(
                        select(Interest.slug)
                        .join(BoardInterest, BoardInterest.interest_id == Interest.id)
                        .where(BoardInterest.board_id == UUID(other["id"]))
                        .order_by(BoardInterest.position)
                    )
                ).all()
            )

    assert r.client.portal.call(stored_other_interests) == original
    assert r.client.get(other_path).json()["board"]["interest_ids"] == [
        slug for slug in original if slug != "development"
    ]


def test_failed_commit_rolls_back_settings_interest_links_revision_and_audit(roster):
    r = roster
    before = settings_snapshot(r)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        response = change(
            r,
            name="저장 실패",
            rules="변경",
            interest_ids=[],
            visibility="private",
            join_policy="invite",
            status="archived",
        )
    assert response.status_code == 503, response.text
    assert settings_snapshot(r) == before
