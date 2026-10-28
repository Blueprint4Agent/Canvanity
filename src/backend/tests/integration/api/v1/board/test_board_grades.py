from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import (
    Board,
    BoardMember,
    BoardMemberAudit,
    BoardMemberGrade,
    BoardPolicy,
    Shelf,
    ShelfPolicy,
)
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import roster as roster, window

pytestmark = pytest.mark.primary_data


def listing(r):
    response = r.client.get(r.path + "/grades", headers=r.headers["owner"])
    assert response.status_code == 200, response.text
    return response.json()


def mutate(r, method, suffix="", actor="owner", **changes):
    return r.client.request(
        method,
        r.path + "/grades" + suffix,
        headers=r.headers[actor],
        json={
            "expected_revision": listing(r)["board_revision"],
            "reason": "등급 구성 변경",
            **changes,
        },
    )


def snapshot(r):
    async def read():
        async with get_db() as db:
            board_id = UUID(r.board["id"])
            grades = (
                await db.scalars(
                    select(BoardMemberGrade)
                    .where(BoardMemberGrade.board_id == board_id)
                    .order_by(BoardMemberGrade.id)
                )
            ).all()
            members = (
                await db.scalars(
                    select(BoardMember)
                    .where(BoardMember.board_id == board_id)
                    .order_by(BoardMember.user_id)
                )
            ).all()
            board_policies = (
                await db.scalars(
                    select(BoardPolicy)
                    .where(BoardPolicy.board_id == board_id)
                    .order_by(BoardPolicy.action)
                )
            ).all()
            shelf_policies = (
                await db.scalars(
                    select(ShelfPolicy)
                    .where(ShelfPolicy.board_id == board_id)
                    .order_by(ShelfPolicy.shelf_id, ShelfPolicy.action)
                )
            ).all()
            audits = (
                await db.scalars(
                    select(BoardMemberAudit)
                    .where(BoardMemberAudit.board_id == board_id)
                    .order_by(BoardMemberAudit.id)
                )
            ).all()
            return (
                (await db.get(Board, board_id)).revision,
                [(str(g.id), g.name, g.rank, g.is_default) for g in grades],
                [(m.user_id, str(m.grade_id), m.role, m.status) for m in members],
                [(p.action, str(p.min_grade_id)) for p in board_policies],
                [(str(p.shelf_id), p.action, str(p.min_grade_id)) for p in shelf_policies],
                [(str(a.id), a.action, a.changes) for a in audits],
            )

    return r.client.portal.call(read)


def test_public_and_private_grade_listing_respects_current_access(roster):
    r = roster
    public = r.client.get(r.path + "/grades")
    assert public.status_code == 200
    assert public.headers["cache-control"] == "private, no-store"
    assert all(set(g) == {"id", "name", "rank", "is_default"} for g in public.json()["items"])
    private = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={
            **PAYLOAD,
            "slug": "private-grades",
            "visibility": "private",
            "join_policy": "invite",
        },
    ).json()
    path = f"/api/v1/boards/{private['id']}/grades"
    assert r.client.get(path).status_code == 404
    assert r.client.get(path, headers=r.headers["outsider"]).status_code == 404
    assert r.client.get(path, headers=r.headers["owner"]).status_code == 200


@pytest.mark.parametrize("actor", ["moderator", "member", "outsider"])
def test_grade_management_requires_board_owner_or_admin(roster, actor):
    r = roster
    before = snapshot(r)
    grade_id = r.grades[0]["id"]
    for method, suffix, changes in [
        ("POST", "", {"name": "새 등급", "rank": 30}),
        ("PATCH", f"/{grade_id}", {"name": "이름 변경"}),
        ("PATCH", "/order", {"grade_ids": [g["id"] for g in r.grades][::-1]}),
        ("DELETE", f"/{grade_id}", {"replacement_grade_id": r.grades[1]["id"]}),
    ]:
        assert mutate(r, method, suffix, actor, **changes).status_code == 403
    assert snapshot(r) == before


@pytest.mark.parametrize("state", ["suspended", "banned", "pending", "archived"])
def test_revoked_admin_and_archived_board_cannot_change_grades(roster, state):
    r = roster

    async def revoke():
        async with get_db() as db:
            if state == "archived":
                (await db.get(Board, UUID(r.board["id"]))).status = state
            else:
                (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["admin"]))).status = state
            await db.commit()

    r.client.portal.call(revoke)
    before = snapshot(r)
    response = mutate(r, "POST", actor="admin", name="불가", rank=30)
    assert response.status_code == (404 if state in {"suspended", "banned"} else 403)
    assert snapshot(r) == before


def test_name_default_and_reorder_keep_ids_and_roles_and_apply_to_current_policies(roster):
    r = roster
    first, second, third = [g["id"] for g in r.grades]
    before = listing(r)["board_revision"]
    changed = mutate(r, "PATCH", f"/{first}", "admin", name="  새로운 시작  ")
    assert changed.status_code == 200, changed.text
    assert changed.json()["grade"] == {**r.grades[0], "name": "새로운 시작"}
    assert changed.json()["board_revision"] == before + 1
    selected = mutate(r, "PATCH", f"/{second}", "admin", is_default=True)
    assert selected.status_code == 200, selected.text
    member_home = r.client.get(r.path + "/home", headers=r.headers["member"]).json()
    assert member_home["membership"]["grade_id"] == first
    assert not member_home["shelves"][1]["capabilities"]["create_canvas"]
    joined = r.client.post(r.path + "/join", headers=r.headers["outsider"])
    assert joined.json()["grade_id"] == second and joined.json()["role"] == "member"
    reordered = mutate(r, "PATCH", "/order", grade_ids=[second, third, first])
    assert reordered.status_code == 200, reordered.text
    assert [g["rank"] for g in reordered.json()["items"]] == [0, 10, 20]
    current = r.client.get(r.path + "/home", headers=r.headers["member"]).json()
    assert current["shelves"][1]["capabilities"]["create_canvas"]
    assert current["membership"]["role"] == "member" and current["membership"]["grade_id"] == first
    assert r.client.get(r.path + "/members", headers=r.headers["member"]).status_code == 403
    before = snapshot(r)
    assert mutate(r, "PATCH", "/order", grade_ids=[second, third, first]).status_code == 200
    assert mutate(r, "PATCH", f"/{first}", name="새로운 시작").status_code == 200
    assert mutate(r, "PATCH", f"/{second}", is_default=True).status_code == 200
    assert snapshot(r) == before


def test_grade_create_uniqueness_limit_and_integer_boundary(roster):
    r = roster
    created = mutate(r, "POST", name="최상위", rank=2**31 - 1)
    assert created.status_code == 201, created.text
    for name, rank, error in [
        ("최상위", 30, "BOARD_GRADE_NAME_TAKEN"),
        ("다른 등급", 10, "BOARD_GRADE_RANK_TAKEN"),
    ]:
        before = snapshot(r)
        rejected = mutate(r, "POST", name=name, rank=rank)
        assert rejected.status_code == 409 and rejected.json()["detail"]["error"] == error
        assert snapshot(r) == before
    for index in range(16):
        assert mutate(r, "POST", name=f"등급 {index}", rank=30 + index).status_code == 201
    assert len(listing(r)["items"]) == 20
    before = snapshot(r)
    assert (
        mutate(r, "POST", name="초과", rank=500).json()["detail"]["error"]
        == "BOARD_GRADE_LIMIT_REACHED"
    )
    assert snapshot(r) == before
    reversed_ids = [g["id"] for g in listing(r)["items"]][::-1]
    result = mutate(r, "PATCH", "/order", grade_ids=reversed_ids)
    assert result.status_code == 200, result.text
    assert [g["rank"] for g in result.json()["items"]] == list(range(0, 200, 10))


def test_invalid_changes_never_partially_update_or_reveal_other_board_grades(roster):
    r = roster
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "foreign-grades"}
    ).json()
    foreign = r.client.get(f"/api/v1/boards/{other['id']}/grades").json()["items"][0]["id"]
    before = snapshot(r)
    first, second, third = [g["id"] for g in r.grades]
    for ids in (
        [first],
        [first, second, second],
        [first, second, foreign],
        [first, second, str(uuid4())],
    ):
        assert mutate(r, "PATCH", "/order", grade_ids=ids).status_code == 422
    for replacement in (first, foreign, str(uuid4())):
        assert mutate(r, "DELETE", f"/{first}", replacement_grade_id=replacement).status_code == 422
    for target in (foreign, str(uuid4())):
        assert mutate(r, "PATCH", f"/{target}", name="외부").status_code == 404
        assert mutate(r, "DELETE", f"/{target}", replacement_grade_id=second).status_code == 404
    rejected = mutate(r, "PATCH", f"/{first}", name=r.grades[1]["name"], is_default=True)
    assert rejected.status_code == 409
    stale = mutate(r, "PATCH", f"/{third}", name="변경", expected_revision=0)
    assert (
        stale.status_code == 409
        and stale.json()["detail"]["details"]["current_revision"] == before[0]
    )
    assert snapshot(r) == before


def test_deleting_grade_reassigns_members_and_both_policy_scopes_atomically(roster):
    r = roster
    first, second, third = [g["id"] for g in r.grades]

    async def add_override():
        async with get_db() as db:
            board_id = UUID(r.board["id"])
            shelf_id = await db.scalar(
                select(Shelf.id).where(Shelf.board_id == board_id, Shelf.slug == "general")
            )
            db.add(
                ShelfPolicy(
                    board_id=board_id,
                    shelf_id=shelf_id,
                    action="read_canvas",
                    audience="members",
                    min_grade_id=UUID(first),
                    staff_only=False,
                    staff_bypass=True,
                )
            )
            await db.commit()

    r.client.portal.call(add_override)
    result = mutate(r, "DELETE", f"/{first}", "admin", replacement_grade_id=third)
    assert result.status_code == 200, result.text
    assert [g["id"] for g in result.json()["items"]] == [second, third]
    assert sum(g["is_default"] for g in result.json()["items"]) == 1
    assert result.json()["items"][1]["is_default"]
    state = snapshot(r)
    assert all(m[1] == third for m in state[2])
    assert all(p[1] != first for p in state[3]) and all(p[2] != first for p in state[4])
    audits = r.client.get(
        r.path + "/member-audit", headers=r.headers["owner"], params=window()
    ).json()["items"]
    audit = next(a for a in audits if a["action"] == "grade_deleted")
    assert audit["target_user_id"] is None and audit["before"] is None
    change = audit["grade_change"]
    assert change["replacement_grade_id"] == third
    assert change["reassigned_members"] == 5 and change["reassigned_board_policies"] > 0
    assert change["reassigned_shelf_policies"] == 1
    assert len(change["before"]) == 3 and len(change["after"]) == 2
    assert mutate(r, "DELETE", f"/{second}", replacement_grade_id=third).status_code == 200
    before = snapshot(r)
    rejected = mutate(r, "DELETE", f"/{third}", replacement_grade_id=third)
    assert rejected.status_code == 409 and rejected.json()["detail"]["error"] == "BOARD_LAST_GRADE"
    assert snapshot(r) == before


@pytest.mark.parametrize("operation", ["default", "order", "delete"])
def test_failed_commit_rolls_back_default_ranks_references_revision_and_audit(roster, operation):
    r = roster
    first, second, third = [g["id"] for g in r.grades]
    before = snapshot(r)
    cases = {
        "default": ("PATCH", f"/{second}", {"is_default": True, "name": "기본 변경"}),
        "order": ("PATCH", "/order", {"grade_ids": [third, second, first]}),
        "delete": ("DELETE", f"/{first}", {"replacement_grade_id": second}),
    }
    method, suffix, changes = cases[operation]
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        response = mutate(r, method, suffix, **changes)
    assert response.status_code == 503, response.text
    assert snapshot(r) == before
