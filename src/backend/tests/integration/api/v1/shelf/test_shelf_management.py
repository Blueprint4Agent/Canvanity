from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import (
    ACTIONS,
    ActionPolicy,
    Board,
    BoardMember,
    BoardMemberAudit,
    BoardPolicy,
    Shelf,
    ShelfPolicy,
    ShelfState,
)
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import (
    revision,
    roster as roster,
    window,
)

pytestmark = pytest.mark.primary_data


def listing(r, actor="owner", manage=True):
    result = r.client.get(r.path + "/shelves", headers=r.headers[actor], params={"manage": manage})
    assert result.status_code == 200, result.text
    return result.json()


def write(r, method, path, actor="owner", **fields):
    return r.client.request(
        method,
        path,
        headers=r.headers[actor],
        json={"expected_revision": revision(r), "reason": "분류와 정책 변경", **fields},
    )


def path(shelf):
    return f"/api/v1/shelves/{shelf['id']}"


def defaults(r):
    return r.client.get(r.path + "/policies", headers=r.headers["owner"]).json()["actions"]


def member_policy(grade_id, bypass=True):
    return {
        "audience": "members",
        "min_grade_id": grade_id,
        "staff_only": False,
        "staff_bypass": bypass,
    }


def snapshot(r):
    async def read():
        async with get_db() as db:
            board_id = UUID(r.board["id"])
            shelves = (
                await db.scalars(select(Shelf).where(Shelf.board_id == board_id).order_by(Shelf.id))
            ).all()
            policies = (
                await db.scalars(
                    select(BoardPolicy)
                    .where(BoardPolicy.board_id == board_id)
                    .order_by(BoardPolicy.action)
                )
            ).all()
            overrides = (
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
                [ShelfState.model_validate(s).model_dump(mode="json") for s in shelves],
                [
                    (p.action, ActionPolicy.model_validate(p).model_dump(mode="json"))
                    for p in policies
                ],
                [
                    (
                        str(p.shelf_id),
                        p.action,
                        ActionPolicy.model_validate(p).model_dump(mode="json"),
                    )
                    for p in overrides
                ],
                [(str(a.id), a.action, a.changes) for a in audits],
            )

    return r.client.portal.call(read)


def test_crud_hidden_direct_read_order_and_typed_audit(roster):
    r = roster
    created = write(
        r, "POST", r.path + "/shelves", "admin", name="  프로젝트  ", slug="projects", icon="blocks"
    )
    assert created.status_code == 201, created.text
    data = created.json()
    shelf = data["shelf"]
    assert shelf["name"] == "프로젝트" and shelf["sort_order"] == 2 and not shelf["is_default"]
    assert created.headers["location"] == path(shelf)
    assert shelf["capabilities"] == {a: True for a in ACTIONS}
    hidden = write(r, "PATCH", path(shelf), name="숨긴 프로젝트", is_visible=False)
    assert hidden.status_code == 200
    before = snapshot(r)
    noop = write(r, "PATCH", path(shelf), name="숨긴 프로젝트")
    assert noop.status_code == 200 and snapshot(r) == before
    assert r.client.get(path(shelf)).status_code == 200
    assert shelf["id"] not in [s["id"] for s in r.client.get(r.path + "/shelves").json()["items"]]
    assert shelf["id"] not in [s["id"] for s in r.client.get(r.path + "/home").json()["shelves"]]
    ids = [s["id"] for s in listing(r)["items"]][::-1]
    ordered = write(r, "PATCH", r.path + "/shelves/order", "admin", shelf_ids=ids)
    assert ordered.status_code == 200
    assert [s["id"] for s in ordered.json()["items"]] == ids
    assert [s["sort_order"] for s in ordered.json()["items"]] == [0, 1, 2]
    unchanged = snapshot(r)
    assert write(r, "PATCH", r.path + "/shelves/order", shelf_ids=ids).status_code == 200
    assert snapshot(r) == unchanged
    removed = write(r, "DELETE", path(shelf))
    assert removed.status_code == 204 and removed.content == b""
    assert int(removed.headers["x-board-revision"]) == revision(r)
    assert r.client.get(path(shelf)).status_code == 404
    audits = r.client.get(
        r.path + "/member-audit", headers=r.headers["owner"], params=window()
    ).json()["items"]
    changes = [a for a in audits if a["shelf_change"]]
    assert {a["action"] for a in changes} == {
        "shelf_created",
        "shelf_updated",
        "shelves_reordered",
        "shelf_deleted",
    }
    for audit in changes:
        assert audit["before"] is None and audit["after"] is None
        assert audit["target_user_id"] is None
        assert set(audit["shelf_change"]) == {
            "before",
            "after",
            "policies_before",
            "policies_after",
        }
        for state in audit["shelf_change"]["before"] + audit["shelf_change"]["after"]:
            assert set(state) == set(ShelfState.model_fields)


@pytest.mark.parametrize("actor", ["moderator", "member", "outsider"])
def test_management_uses_board_roles_and_rejects_global_admin(roster, actor):
    r = roster
    shelf = listing(r)["items"][1]
    before = snapshot(r)
    assert (
        r.client.get(
            r.path + "/shelves", headers=r.headers[actor], params={"manage": True}
        ).status_code
        == 403
    )
    for target in (r.path + "/policies", path(shelf) + "/policies"):
        assert r.client.get(target, headers=r.headers[actor]).status_code == 403
        assert write(r, "PUT", target, actor, actions=defaults(r)).status_code == 403
    for method, target, fields in [
        ("POST", r.path + "/shelves", {"name": "불가", "slug": "denied"}),
        ("PATCH", path(shelf), {"name": "불가"}),
        ("DELETE", path(shelf), {}),
        (
            "PATCH",
            r.path + "/shelves/order",
            {"shelf_ids": [s["id"] for s in listing(r)["items"]][::-1]},
        ),
    ]:
        assert write(r, method, target, actor, **fields).status_code == 403
    assert snapshot(r) == before


@pytest.mark.parametrize("state", ["pending", "suspended", "banned", "archived", "board_suspended"])
def test_current_status_revokes_management_without_reissuing_token(roster, state):
    r = roster

    async def change():
        async with get_db() as db:
            if state in {"archived", "board_suspended"}:
                (await db.get(Board, UUID(r.board["id"]))).status = (
                    "suspended" if state == "board_suspended" else state
                )
            else:
                (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["admin"]))).status = state
            await db.commit()

    r.client.portal.call(change)
    before = snapshot(r)
    response = r.client.post(
        r.path + "/shelves",
        headers=r.headers["admin"],
        json={
            "expected_revision": before[0],
            "reason": "상태 확인",
            "name": "불가",
            "slug": "denied",
        },
    )
    assert response.status_code == (
        404 if state in {"suspended", "banned", "board_suspended"} else 403
    )
    assert snapshot(r) == before
    if state == "archived":
        assert r.client.get(r.path + "/policies", headers=r.headers["admin"]).status_code == 200
        for shelf in r.client.get(r.path + "/shelves").json()["items"]:
            assert not any(
                value for action, value in shelf["capabilities"].items() if action != "read_canvas"
            )


def test_restricted_shelf_is_filtered_and_promotion_demotion_and_rank_apply_immediately(roster):
    r = roster
    general = listing(r)["items"][1]
    actions = {a: None for a in ACTIONS}
    actions["read_canvas"] = member_policy(r.grades[2]["id"], False)
    response = write(r, "PUT", path(general) + "/policies", actions=actions)
    assert response.status_code == 200, response.text
    assert r.client.get(path(general)).status_code == 404
    assert r.client.get(path(general), headers=r.headers["owner"]).status_code == 404
    assert not next(s for s in listing(r)["items"] if s["id"] == general["id"])["capabilities"][
        "read_canvas"
    ]
    for suffix, key in (("/shelves", "items"), ("/home", "shelves")):
        items = r.client.get(r.path + suffix, headers=r.headers["member"]).json()[key]
        assert general["id"] not in [s["id"] for s in items]
    promoted = write(r, "PATCH", r.path + f"/members/{r.ids['member']}", grade_id=r.grades[2]["id"])
    assert promoted.status_code == 200
    allowed = r.client.get(path(general), headers=r.headers["member"])
    assert allowed.status_code == 200 and allowed.json()["shelf"]["capabilities"]["create_canvas"]
    assert (
        write(
            r, "POST", r.path + "/shelves", "member", name="등급은 운영 권한이 아님", slug="denied"
        ).status_code
        == 403
    )
    assert (
        write(
            r, "PATCH", r.path + f"/members/{r.ids['member']}", grade_id=r.grades[0]["id"]
        ).status_code
        == 200
    )
    assert r.client.get(path(general), headers=r.headers["member"]).status_code == 404
    assert (
        write(
            r,
            "PATCH",
            r.path + "/grades/order",
            grade_ids=[r.grades[2]["id"], r.grades[1]["id"], r.grades[0]["id"]],
        ).status_code
        == 200
    )
    assert r.client.get(path(general), headers=r.headers["member"]).status_code == 200


def test_policy_inheritance_noop_current_capabilities_and_typed_audit(roster):
    r = roster
    general = listing(r)["items"][1]
    inherited = {a: None for a in ACTIONS}
    actions = {**inherited, "create_canvas": member_policy(r.grades[2]["id"], False)}
    assert write(r, "PUT", path(general) + "/policies", actions=actions).status_code == 200
    board_actions = defaults(r)
    board_actions["create_canvas"] = member_policy(r.grades[0]["id"])
    assert write(r, "PUT", r.path + "/policies", actions=board_actions).status_code == 200
    item = r.client.get(path(general), headers=r.headers["member"]).json()["shelf"]
    assert not item["capabilities"]["create_canvas"]
    reset = write(r, "PUT", path(general) + "/policies", actions=inherited)
    assert reset.status_code == 200 and reset.json()["actions"] == inherited
    assert reset.json()["effective_actions"] == board_actions
    assert r.client.get(path(general), headers=r.headers["member"]).json()["shelf"]["capabilities"][
        "create_canvas"
    ]
    before = snapshot(r)
    assert write(r, "PUT", r.path + "/policies", actions=board_actions).status_code == 200
    assert write(r, "PUT", path(general) + "/policies", actions=inherited).status_code == 200
    assert snapshot(r) == before
    stale = write(
        r, "PUT", r.path + "/policies", expected_revision=before[0] - 1, actions=board_actions
    )
    assert stale.status_code == 409 and snapshot(r) == before
    audits = r.client.get(
        r.path + "/member-audit", headers=r.headers["owner"], params=window()
    ).json()["items"]
    changes = [a for a in audits if a["policy_change"]]
    assert len(changes) == 3
    for a in changes:
        assert a["before"] is None and a["after"] is None
        assert set(a["policy_change"]) == {"shelf_id", "before", "after"}
        assert set(a["policy_change"]["after"]) == set(ACTIONS)


def test_notice_restrictions_and_purpose_conversion_preserve_other_overrides(roster):
    r = roster
    general = listing(r)["items"][1]
    assert write(r, "PATCH", path(general), purpose="notice").status_code == 200
    response = r.client.get(path(general) + "/policies", headers=r.headers["owner"])
    policies = response.json()["actions"]
    assert all(policies[a]["staff_only"] for a in ("create_canvas", "create_comment"))
    for actor in ("owner", "admin", "moderator"):
        assert r.client.get(path(general), headers=r.headers[actor]).json()["shelf"][
            "capabilities"
        ]["create_canvas"]
    assert (
        write(
            r, "PATCH", r.path + f"/members/{r.ids['member']}", grade_id=r.grades[2]["id"]
        ).status_code
        == 200
    )
    assert not r.client.get(path(general), headers=r.headers["member"]).json()["shelf"][
        "capabilities"
    ]["create_canvas"]
    before = snapshot(r)
    assert (
        write(r, "PUT", path(general) + "/policies", actions={a: None for a in ACTIONS}).status_code
        == 422
    )
    assert snapshot(r) == before
    assert write(r, "PATCH", path(general), purpose="general").status_code == 200
    assert (
        write(r, "PUT", path(general) + "/policies", actions={a: None for a in ACTIONS}).status_code
        == 200
    )
    assert r.client.get(path(general), headers=r.headers["member"]).json()["shelf"]["capabilities"][
        "create_canvas"
    ]
    created = write(r, "POST", r.path + "/shelves", name="추가 공지", slug="news", purpose="notice")
    assert created.status_code == 201
    assert not r.client.get(path(created.json()["shelf"]), headers=r.headers["member"]).json()[
        "shelf"
    ]["capabilities"]["create_comment"]


def test_same_board_slug_grade_order_and_delete_protection(roster):
    r = roster
    items = listing(r)["items"]
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "other-shelf-board"}
    ).json()
    other_home = r.client.get(
        f"/api/v1/boards/{other['id']}/home", headers=r.headers["owner"]
    ).json()
    before = snapshot(r)
    assert write(r, "POST", r.path + "/shelves", name="중복", slug="general").status_code == 409
    assert write(r, "PATCH", path(items[0]), slug="general").status_code == 409
    assert (
        write(r, "PATCH", r.path + "/shelves/order", shelf_ids=[items[0]["id"]]).status_code == 422
    )
    assert (
        write(
            r,
            "PATCH",
            r.path + "/shelves/order",
            shelf_ids=[items[0]["id"], other_home["shelves"][0]["id"]],
        ).status_code
        == 422
    )
    invalid = {**defaults(r), "read_canvas": member_policy(other_home["grades"][0]["id"])}
    assert write(r, "PUT", r.path + "/policies", actions=invalid).status_code == 422
    assert write(r, "PUT", path(items[1]) + "/policies", actions=invalid).status_code == 422
    assert write(r, "DELETE", path(items[1])).status_code == 409
    assert snapshot(r) == before
    # The same slug is valid in another Board, while foreign management still fails.
    assert r.client.get(f"/api/v1/boards/{other['id']}/shelves").status_code == 200
    assert (
        r.client.patch(
            f"/api/v1/shelves/{other_home['shelves'][0]['id']}",
            headers=r.headers["outsider"],
            json={"expected_revision": 0, "reason": "타 보드", "name": "불가"},
        ).status_code
        == 403
    )


def test_private_board_and_last_shelf_guard(roster):
    r = roster
    other = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={**PAYLOAD, "slug": "private-shelf", "visibility": "private", "join_policy": "invite"},
    ).json()
    other_path = f"/api/v1/boards/{other['id']}"
    home = r.client.get(other_path + "/home", headers=r.headers["owner"]).json()
    shelf_path = path(home["shelves"][1])
    for headers in ({}, r.headers["outsider"]):
        assert r.client.get(other_path + "/shelves", headers=headers).status_code == 404
        hidden = r.client.get(shelf_path, headers=headers)
        missing = r.client.get(f"/api/v1/shelves/{uuid4()}", headers=headers)
        assert hidden.status_code == missing.status_code == 404
        assert hidden.json()["detail"] == missing.json()["detail"]
    items = listing(r)["items"]
    assert write(r, "DELETE", path(items[0])).status_code == 204

    async def clear_default():
        async with get_db() as db:
            (await db.get(Shelf, UUID(items[1]["id"]))).is_default = False
            await db.commit()

    r.client.portal.call(clear_default)
    assert write(r, "DELETE", path(items[1])).status_code == 409


@pytest.mark.parametrize(
    "operation", ["create", "change", "reorder", "delete", "board_policy", "shelf_policy"]
)
def test_commit_failure_rolls_back_shelves_policies_revision_and_audit(roster, operation):
    r = roster
    items = listing(r)["items"]
    board_actions = {**defaults(r), "react": member_policy(r.grades[2]["id"])}
    actions = {a: None for a in ACTIONS}
    actions["react"] = member_policy(r.grades[2]["id"])
    method, target, fields = {
        "create": (
            "POST",
            r.path + "/shelves",
            {"name": "롤백", "slug": "rollback", "purpose": "notice"},
        ),
        "change": ("PATCH", path(items[1]), {"purpose": "notice"}),
        "reorder": (
            "PATCH",
            r.path + "/shelves/order",
            {"shelf_ids": [s["id"] for s in items][::-1]},
        ),
        "delete": ("DELETE", path(items[0]), {}),
        "board_policy": ("PUT", r.path + "/policies", {"actions": board_actions}),
        "shelf_policy": ("PUT", path(items[1]) + "/policies", {"actions": actions}),
    }[operation]
    before = snapshot(r)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        response = write(r, method, target, **fields)
    assert response.status_code == 503, response.text
    assert response.json()["detail"]["error"] == "BOARD_UNAVAILABLE"
    assert snapshot(r) == before


def test_board_shelf_limit_is_enforced(roster):
    r = roster

    async def populate():
        async with get_db() as db:
            db.add_all(
                [
                    Shelf(
                        board_id=UUID(r.board["id"]),
                        name=f"분류 {i}",
                        slug=f"shelf-{i}",
                        purpose="general",
                        sort_order=i + 2,
                    )
                    for i in range(98)
                ]
            )
            await db.commit()

    r.client.portal.call(populate)
    before = snapshot(r)
    response = write(r, "POST", r.path + "/shelves", name="초과", slug="too-many")
    assert (
        response.status_code == 409 and response.json()["detail"]["error"] == "SHELF_LIMIT_REACHED"
    )
    assert snapshot(r) == before
    assert len(listing(r)["items"]) == 100
