from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import Board, BoardMember, BoardMemberAudit
from app.models.user import User
from tests.integration.api.v1.board.test_board_creation import PAYLOAD, signup

pytestmark = pytest.mark.primary_data


@pytest.fixture
def roster(integration_client):
    client = integration_client
    headers, ids = {}, {}
    for name in ("owner", "admin", "moderator", "member", "peer", "outsider"):
        headers[name], ids[name] = signup(client, "operations-" + name)
    board = client.post("/api/v1/boards", json=PAYLOAD, headers=headers["owner"]).json()
    path = f"/api/v1/boards/{board['id']}"
    for name in ("admin", "moderator", "member", "peer"):
        assert client.post(path + "/join", headers=headers[name]).status_code == 200
    for name in ("admin", "moderator"):
        revision = client.get(path + "/home", headers=headers["owner"]).json()["board"]["revision"]
        result = client.patch(
            path + f"/members/{ids[name]}",
            headers=headers["owner"],
            json={"expected_revision": revision, "reason": "운영진 구성", "role": name},
        )
        assert result.status_code == 200, result.text
    grades = client.get(path + "/home", headers=headers["owner"]).json()["grades"]

    async def global_admin():
        async with get_db() as db:
            (await db.get(User, ids["outsider"])).role = "admin"
            await db.commit()

    client.portal.call(global_admin)
    return SimpleNamespace(
        client=client, board=board, path=path, headers=headers, ids=ids, grades=grades
    )


def revision(r):
    return r.client.get(r.path + "/home", headers=r.headers["owner"]).json()["board"]["revision"]


def mutate(r, actor="owner", target="member", **changes):
    body = {"expected_revision": revision(r), "reason": "회원 운영 변경", **changes}
    return r.client.patch(r.path + f"/members/{r.ids[target]}", headers=r.headers[actor], json=body)


def snapshot(r):
    async def read():
        async with get_db() as db:
            members = (
                await db.scalars(
                    select(BoardMember)
                    .where(BoardMember.board_id == UUID(r.board["id"]))
                    .order_by(BoardMember.user_id)
                )
            ).all()
            audit = (
                await db.scalars(
                    select(BoardMemberAudit)
                    .where(BoardMemberAudit.board_id == UUID(r.board["id"]))
                    .order_by(BoardMemberAudit.id)
                )
            ).all()
            return (
                (await db.get(Board, UUID(r.board["id"]))).revision,
                [(m.user_id, m.role, m.status, str(m.grade_id)) for m in members],
                [(str(a.id), a.action, a.changes) for a in audit],
            )

    return r.client.portal.call(read)


def window():
    now = datetime.now(UTC)
    return {
        "since": (now - timedelta(days=1)).isoformat(),
        "until": (now + timedelta(days=1)).isoformat(),
    }


@pytest.mark.parametrize(
    "actor,target,change,expected",
    [
        ("owner", "member", {"role": "admin"}, 200),
        ("admin", "member", {"role": "moderator"}, 200),
        ("admin", "admin", {"status": "banned"}, 403),
        ("admin", "owner", {"status": "banned"}, 403),
        ("admin", "member", {"role": "admin"}, 403),
        ("moderator", "member", {"status": "suspended"}, 200),
        ("moderator", "member", {"status": "banned"}, 200),
        ("moderator", "member", {"status": "active"}, 403),
        ("moderator", "admin", {"status": "banned"}, 403),
        ("moderator", "member", {"role": "member"}, 403),
        ("member", "peer", {"status": "banned"}, 403),
        ("outsider", "member", {"status": "banned"}, 403),
        ("owner", "owner", {"status": "suspended"}, 403),
        ("owner", "member", {"role": "owner"}, 422),
        ("owner", "member", {"role": "admin", "status": "suspended"}, 422),
        ("owner", "admin", {"status": "banned"}, 200),
        ("admin", "moderator", {"status": "banned"}, 200),
    ],
)
def test_role_and_state_hierarchy(roster, actor, target, change, expected):
    r = roster
    before = snapshot(r)
    response = mutate(r, actor, target, **change)
    assert response.status_code == expected, response.text
    if expected != 200:
        assert snapshot(r) == before
    else:
        assert response.headers["cache-control"] == "private, no-store"
        for key, value in change.items():
            assert response.json()["member"][key] == value
        assert response.json()["board_revision"] == before[0] + 1


def test_grade_is_separate_and_revocation_uses_current_membership(roster):
    r = roster
    assert mutate(r, "admin", grade_id=r.grades[1]["id"]).status_code == 200
    home = r.client.get(r.path + "/home", headers=r.headers["member"]).json()
    assert home["membership"]["role"] == "member"
    assert home["shelves"][1]["capabilities"]["create_canvas"]
    assert r.client.get(r.path + "/members", headers=r.headers["member"]).status_code == 403
    assert mutate(r, grade_id=r.grades[0]["id"]).status_code == 200
    assert not r.client.get(r.path + "/home", headers=r.headers["member"]).json()["shelves"][1][
        "capabilities"
    ]["create_canvas"]
    assert mutate(r, "moderator", status="banned").status_code == 200
    assert r.client.get(r.path + "/home", headers=r.headers["member"]).status_code == 404
    assert r.client.post(r.path + "/join", headers=r.headers["member"]).status_code == 403
    assert mutate(r, "moderator", status="active").status_code == 403
    assert mutate(r, "admin", status="active").status_code == 200
    assert r.client.get(r.path + "/home", headers=r.headers["member"]).status_code == 200


def test_all_fields_authorized_before_atomic_update(roster):
    r = roster
    before = snapshot(r)
    assert mutate(r, "admin", grade_id=r.grades[1]["id"], role="admin").status_code == 403
    assert snapshot(r) == before
    assert mutate(r, "moderator", status="banned", grade_id=r.grades[0]["id"]).status_code == 403
    assert snapshot(r) == before
    assert mutate(r, "moderator", grade_id=r.grades[2]["id"]).status_code == 403
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "other-operations"}
    ).json()
    foreign = r.client.get(f"/api/v1/boards/{other['id']}/home", headers=r.headers["owner"]).json()[
        "grades"
    ][0]["id"]
    assert mutate(r, grade_id=foreign, status="suspended").status_code == 422
    assert snapshot(r) == before


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"role": None},
        {"status": None},
        {"grade_id": None},
        {"reason": "  ", "status": "banned"},
        {"reason": "a" * 501, "status": "banned"},
        {"status": "pending"},
        {"owner_id": 999, "status": "active"},
        {"expected_revision": -1, "status": "banned"},
    ],
)
def test_invalid_mutations_never_write(roster, changes):
    r = roster
    before = snapshot(r)
    assert mutate(r, **changes).status_code == 422
    assert snapshot(r) == before


def test_revision_noop_and_commit_failure_roll_back(roster):
    r = roster
    before = snapshot(r)
    assert mutate(r, grade_id=r.grades[0]["id"]).status_code == 200
    assert snapshot(r) == before
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit",
        side_effect=SQLAlchemyError("controlled failure"),
    ):
        result = mutate(r, role="admin", grade_id=r.grades[2]["id"])
    assert result.status_code == 503
    assert snapshot(r) == before
    assert mutate(r, status="suspended").status_code == 200
    stale = r.client.patch(
        r.path + f"/members/{r.ids['member']}",
        headers=r.headers["owner"],
        json={"expected_revision": before[0], "reason": "old", "status": "active"},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["details"]["current_revision"] == before[0] + 1


def test_lists_moderator_redaction_and_literal_search(roster):
    r = roster
    page = r.client.get(r.path + "/members?limit=2", headers=r.headers["admin"])
    assert page.status_code == 200, page.text
    seen, cursor = [], None
    while True:
        data = r.client.get(
            r.path + "/members",
            params={"limit": 2, **({"cursor": cursor} if cursor else {})},
            headers=r.headers["owner"],
        ).json()
        seen += [item["user_id"] for item in data["items"]]
        cursor = data["next_cursor"]
        if not cursor:
            break
    assert len(seen) == len(set(seen)) == 5
    assert r.ids["outsider"] not in seen
    body = page.text.lower()
    assert "email" not in body and "password" not in body and "token" not in body
    targets = r.client.get(r.path + "/members", headers=r.headers["moderator"]).json()
    assert targets["scope"] == "moderation"
    assert {item["user_id"] for item in targets["items"]} == {r.ids["member"], r.ids["peer"]}
    assert all(set(item) == {"user_id", "name", "handle"} for item in targets["items"])
    assert (
        r.client.get(r.path + "/members?role=admin", headers=r.headers["moderator"]).json()["items"]
        == []
    )

    async def rename():
        async with get_db() as db:
            (await db.get(User, r.ids["member"])).name = "literal%_member"
            await db.commit()

    r.client.portal.call(rename)
    exact = r.client.get(r.path + "/members", params={"q": "%_"}, headers=r.headers["owner"]).json()
    assert [item["user_id"] for item in exact["items"]] == [r.ids["member"]]
    old = page.json()["next_cursor"]
    assert (
        r.client.get(
            r.path + "/members",
            params={"cursor": old, "q": "different"},
            headers=r.headers["admin"],
        ).status_code
        == 422
    )
    assert (
        r.client.get(
            r.path + "/members", params={"cursor": "not-json"}, headers=r.headers["owner"]
        ).status_code
        == 422
    )


def test_audit_window_pagination_redaction_and_current_permissions(roster):
    r = roster
    assert mutate(r, grade_id=r.grades[1]["id"]).status_code == 200
    params = window()
    response = r.client.get(
        r.path + "/member-audit",
        params={**params, "target_user_id": r.ids["member"]},
        headers=r.headers["admin"],
    )
    assert response.status_code == 200, response.text
    latest = response.json()["items"][0]
    assert (
        latest["action"] == "member_updated" and latest["before"]["grade_id"] == r.grades[0]["id"]
    )
    assert latest["after"]["grade_id"] == r.grades[1]["id"] and latest["reason"] == "회원 운영 변경"
    seen, cursor = [], None
    while True:
        data = r.client.get(
            r.path + "/member-audit",
            params={**params, "limit": 2, **({"cursor": cursor} if cursor else {})},
            headers=r.headers["owner"],
        ).json()
        seen += [item["id"] for item in data["items"]]
        cursor = data["next_cursor"]
        if not cursor:
            break
    assert len(seen) == len(set(seen)) == 8
    assert all(word not in response.text.lower() for word in ("email", "password", "token"))
    assert (
        r.client.get(
            r.path + "/member-audit", params=params, headers=r.headers["moderator"]
        ).status_code
        == 403
    )
    naive = {"since": "2026-01-01T00:00:00", "until": "2026-01-02T00:00:00"}
    assert (
        r.client.get(r.path + "/member-audit", params=naive, headers=r.headers["owner"]).status_code
        == 422
    )
    too_long = {"since": "2025-01-01T00:00:00Z", "until": "2026-01-01T00:00:00Z"}
    assert (
        r.client.get(
            r.path + "/member-audit", params=too_long, headers=r.headers["owner"]
        ).status_code
        == 422
    )
    assert mutate(r, "owner", "admin", role="member").status_code == 200
    assert r.client.get(r.path + "/members", headers=r.headers["admin"]).status_code == 403
    assert (
        r.client.get(
            r.path + "/member-audit", params=params, headers=r.headers["admin"]
        ).status_code
        == 403
    )


def test_private_other_board_and_missing_target_guards(roster):
    r = roster
    assert r.client.get(r.path + "/members").status_code == 401
    assert r.client.get(r.path + "/members", headers=r.headers["member"]).status_code == 403
    assert r.client.get(r.path + "/members", headers=r.headers["outsider"]).status_code == 403
    missing = r.client.patch(
        r.path + "/members/999999",
        headers=r.headers["owner"],
        json={"expected_revision": revision(r), "reason": "missing", "status": "banned"},
    )
    assert (
        missing.status_code == 404 and missing.json()["detail"]["error"] == "BOARD_MEMBER_NOT_FOUND"
    )
    private = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={
            **PAYLOAD,
            "slug": "private-management",
            "visibility": "private",
            "join_policy": "invite",
        },
    ).json()
    assert (
        r.client.get(
            f"/api/v1/boards/{private['id']}/members", headers=r.headers["outsider"]
        ).status_code
        == 404
    )
    assert (
        r.client.get(f"/api/v1/boards/{uuid4()}/members", headers=r.headers["owner"]).status_code
        == 404
    )


@pytest.mark.parametrize("state", ["archived", "suspended"])
def test_board_state_and_pending_target_guards(roster, state):
    r = roster

    async def set_state():
        async with get_db() as db:
            (await db.get(Board, UUID(r.board["id"]))).status = state
            await db.commit()

    r.client.portal.call(set_state)
    rev = snapshot(r)[0]
    result = r.client.patch(
        r.path + f"/members/{r.ids['member']}",
        headers=r.headers["owner"],
        json={"expected_revision": rev, "reason": "정지 보드 변경", "status": "banned"},
    )
    assert result.status_code == (403 if state == "archived" else 404)
    assert r.client.get(r.path + "/members", headers=r.headers["owner"]).status_code == (
        200 if state == "archived" else 404
    )


def test_pending_actor_and_targets_do_not_enable_approval(roster):
    r = roster

    async def pending():
        async with get_db() as db:
            (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))).status = "pending"
            await db.commit()

    r.client.portal.call(pending)
    before = snapshot(r)
    assert mutate(r, status="active").status_code == 403
    assert snapshot(r) == before
    assert r.client.get(r.path + "/members", headers=r.headers["member"]).status_code == 403


def test_equal_timestamps_cursor_filters_and_redacted_legacy_audit(roster):
    r = roster

    async def fixture_rows():
        async with get_db() as db:
            for member in (
                await db.scalars(
                    select(BoardMember).where(BoardMember.board_id == UUID(r.board["id"]))
                )
            ).all():
                member.joined_at = datetime(2026, 10, 27, tzinfo=UTC)
            rows = (
                await db.scalars(
                    select(BoardMemberAudit).where(BoardMemberAudit.board_id == UUID(r.board["id"]))
                )
            ).all()
            for row in rows:
                row.created_at = datetime(2026, 10, 27, tzinfo=UTC)
                row.changes = {
                    **row.changes,
                    "email": "private-should-not-leak@example.com",
                    "token": "hidden",
                }
            await db.commit()

    r.client.portal.call(fixture_rows)
    seen, cursor = [], None
    while True:
        data = r.client.get(
            r.path + "/members",
            params={"limit": 1, **({"cursor": cursor} if cursor else {})},
            headers=r.headers["owner"],
        ).json()
        seen += [item["user_id"] for item in data["items"]]
        cursor = data["next_cursor"]
        if not cursor:
            break
    assert seen == sorted(
        [r.ids[name] for name in ("owner", "admin", "moderator", "member", "peer")], reverse=True
    )
    params = {"since": "2026-10-26T00:00:00Z", "until": "2026-10-28T00:00:00Z", "limit": 1}
    data = r.client.get(r.path + "/member-audit", params=params, headers=r.headers["owner"]).json()
    assert "private-should-not-leak" not in str(data)
    assert "token" not in str(data)
    cursor = data["next_cursor"]
    assert cursor
    assert (
        r.client.get(
            r.path + "/member-audit",
            params={**params, "cursor": cursor, "target_user_id": r.ids["member"]},
            headers=r.headers["owner"],
        ).status_code
        == 422
    )
    assert (
        r.client.get(
            r.path + "/members", params={"cursor": cursor}, headers=r.headers["owner"]
        ).status_code
        == 422
    )
    assert r.client.get(r.path + "/members?limit=0", headers=r.headers["owner"]).status_code == 422
    assert (
        r.client.get(r.path + "/members?limit=101", headers=r.headers["owner"]).status_code == 422
    )
    assert (
        r.client.get(
            r.path + "/member-audit",
            params={**params, "since": "2026-10-28T00:00:00Z"},
            headers=r.headers["owner"],
        ).status_code
        == 422
    )


def test_cursor_identity_and_database_id_bounds(roster):
    import base64
    import json

    r = roster
    first = r.client.get(r.path + "/members?limit=1", headers=r.headers["owner"]).json()
    cursor = first["next_cursor"]
    assert cursor
    assert (
        r.client.get(
            r.path + "/members", params={"cursor": cursor}, headers=r.headers["admin"]
        ).status_code
        == 422
    )
    value = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    value["id"] = "9" * 80
    forged = base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
    assert (
        r.client.get(
            r.path + "/members", params={"cursor": forged}, headers=r.headers["owner"]
        ).status_code
        == 422
    )
    invalid = r.client.patch(
        r.path + "/members/999999999999999999999999",
        headers=r.headers["owner"],
        json={"expected_revision": revision(r), "reason": "bad id", "status": "banned"},
    )
    assert invalid.status_code == 404
    assert (
        r.client.get(
            r.path + "/member-audit",
            params={**window(), "target_user_id": 9999999999999999999999},
            headers=r.headers["owner"],
        ).status_code
        == 422
    )


def test_audit_timezone_normalization(roster):
    r = roster
    utc = {"since": "2026-01-01T00:00:00Z", "until": "2026-01-03T00:00:00Z"}
    offset = {"since": "2026-01-01T09:00:00+09:00", "until": "2026-01-03T09:00:00+09:00"}

    async def boundary_event():
        async with get_db() as db:
            row = await db.scalar(
                select(BoardMemberAudit)
                .where(BoardMemberAudit.board_id == UUID(r.board["id"]))
                .order_by(BoardMemberAudit.created_at)
                .limit(1)
            )
            row.created_at = datetime(2026, 1, 1, 1, tzinfo=UTC)
            await db.commit()

    r.client.portal.call(boundary_event)
    # Same instants must produce the same filtering on SQLite and PostgreSQL.
    left = r.client.get(r.path + "/member-audit", params=utc, headers=r.headers["owner"])
    right = r.client.get(r.path + "/member-audit", params=offset, headers=r.headers["owner"])
    assert left.status_code == right.status_code == 200
    assert len(left.json()["items"]) == 1
    assert left.json() == right.json()
