from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.models.board import ACTIONS, Board, BoardMember
from app.models.canvas import Canvas, CanvasDocument, CanvasMetadata
from app.models.user import User, Users
from tests.integration.api.v1.board.test_board_creation import PAYLOAD, signup
from tests.integration.api.v1.board.test_board_member_administration import (
    revision,
    roster as roster,
)

pytestmark = pytest.mark.primary_data


def board_write(r, method, path, actor="owner", **fields):
    return r.client.request(
        method,
        path,
        headers=r.headers[actor],
        json={"expected_revision": revision(r), "reason": "검증용 운영 변경", **fields},
    )


def promote(r, target="member", grade=1):
    response = board_write(
        r, "PATCH", r.path + f"/members/{r.ids[target]}", grade_id=r.grades[grade]["id"]
    )
    assert response.status_code == 200, response.text


def extra_shelf(r, slug="projects"):
    response = board_write(r, "POST", r.path + "/shelves", name="프로젝트", slug=slug)
    assert response.status_code == 201, response.text
    return response.json()["shelf"]


def create(r, *, actor="member", shelf_id=None, **fields):
    return r.client.post(
        r.path + "/canvases",
        headers=r.headers[actor],
        json={"shelf_id": shelf_id or r.shelf_id, "title": "초안 노트", **fields},
    )


@pytest.fixture
def draft(roster):
    r = roster
    r.shelf_id = next(
        s["id"]
        for s in r.client.get(r.path + "/shelves", headers=r.headers["owner"]).json()["items"]
        if s["is_default"]
    )
    promote(r)
    created = create(r, title="  첫 번째 노트  ", visibility="public")
    assert created.status_code == 201, created.text
    r.canvas = created.json()
    r.canvas_path = created.headers["location"]
    return r


def mutate(r, method="PATCH", *, actor="member", suffix="", **fields):
    current = r.client.get(r.canvas_path, headers=r.headers["member"])
    assert current.status_code == 200, current.text
    return r.client.request(
        method,
        r.canvas_path + suffix,
        headers=r.headers[actor],
        json={"expected_revision": current.json()["canvas"]["revision"], **fields},
    )


def snapshot(r):
    async def read():
        async with get_db() as db:
            board_id = UUID(r.board["id"])
            canvases = (
                await db.scalars(
                    select(Canvas).where(Canvas.board_id == board_id).order_by(Canvas.id)
                )
            ).all()
            documents = (
                await db.scalars(
                    select(CanvasDocument)
                    .join(Canvas)
                    .where(Canvas.board_id == board_id)
                    .order_by(CanvasDocument.canvas_id)
                )
            ).all()
            return (
                (await db.get(Board, board_id)).revision,
                [CanvasMetadata.model_validate(c).model_dump(mode="json") for c in canvases],
                [(str(d.canvas_id), d.revision, d.document) for d in documents],
            )

    return r.client.portal.call(read)


def test_atomic_metadata_and_empty_document_have_independent_revisions(draft):
    r = draft
    data = r.canvas
    assert data["canvas"]["title"] == "첫 번째 노트"
    assert data["canvas"]["author_id"] == r.ids["member"]
    assert data["canvas"]["board_id"] == r.board["id"]
    assert data["canvas"]["status"] == "draft" and data["canvas"]["trashed_at"] is None
    assert data["canvas"]["revision"] == data["document_revision"] == 0 and data["view"] == "draft"
    response = r.client.get(r.canvas_path + "/document", headers=r.headers["member"])
    assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
    document = response.json()["document"]
    assert set(document) == {
        "schema_version",
        "engine",
        "settings",
        "nodes",
        "edges",
        "element_order",
    }
    assert document["schema_version"] == 1
    assert document["engine"] == {"name": "excalidraw", "version": "0.18.1", "adapter_version": 1}
    assert document["settings"] == {
        "background": "#F8F7F4",
        "grid": "dots",
        "width": 3200,
        "height": 2100,
    }
    assert document["nodes"] == document["edges"] == document["element_order"] == []
    before = snapshot(r)
    changed = mutate(r, title="수정한 제목", summary="요약", visibility="members")
    assert changed.status_code == 200
    assert changed.json()["canvas"]["revision"] == 1 and changed.json()["document_revision"] == 0
    assert snapshot(r)[0] == before[0] and snapshot(r)[2] == before[2]
    saved = snapshot(r)
    assert mutate(r, title="수정한 제목").status_code == 200 and snapshot(r) == saved
    stale = mutate(r, title="충돌", expected_revision=0)
    assert stale.status_code == 409 and stale.json()["detail"]["details"]["current_revision"] == 1
    assert snapshot(r) == saved
    other = create(r)
    assert other.status_code == 201 and other.json()["canvas"]["visibility"] == "members"


@pytest.mark.parametrize("actor", ["owner", "admin", "moderator", "peer", "outsider"])
def test_operating_roles_and_public_visibility_never_expose_another_authors_draft(draft, actor):
    r = draft
    before = snapshot(r)
    for method, suffix, body in [
        ("GET", "", None),
        ("GET", "/document", None),
        ("PATCH", "", {"expected_revision": 0, "title": "금지"}),
        ("DELETE", "", {"expected_revision": 0}),
        ("POST", "/restore", {"expected_revision": 0}),
    ]:
        denied = r.client.request(
            method, r.canvas_path + suffix, headers=r.headers[actor], json=body
        )
        missing = r.client.request(
            method, f"/api/v1/canvases/{uuid4()}" + suffix, headers=r.headers[actor], json=body
        )
        assert denied.status_code == missing.status_code == 404
        assert denied.json()["detail"] == missing.json()["detail"]
    assert snapshot(r) == before


def test_current_grade_demotion_allows_own_read_and_trash_but_blocks_edit_and_restore(draft):
    r = draft
    promote(r, grade=0)
    own = r.client.get(r.canvas_path, headers=r.headers["member"])
    assert own.status_code == 200
    assert own.json()["capabilities"] == {
        "read_document": True,
        "edit_metadata": False,
        "trash": True,
        "restore": False,
    }
    assert r.client.get(r.canvas_path + "/document", headers=r.headers["member"]).status_code == 200
    assert create(r).status_code == 403
    assert mutate(r, title="등급 미달").status_code == 403
    trashed = mutate(r, "DELETE")
    assert trashed.status_code == 204 and trashed.headers["x-canvas-revision"] == "1"
    own = r.client.get(r.canvas_path, headers=r.headers["member"]).json()
    assert own["canvas"]["status"] == "trashed" and own["canvas"]["trashed_at"].endswith("Z")
    saved = snapshot(r)
    assert mutate(r, "DELETE").status_code == 204 and snapshot(r) == saved
    assert mutate(r, "POST", suffix="/restore").status_code == 403
    promote(r)
    assert mutate(r, title="휴지통 편집 금지").status_code == 409
    restored = mutate(r, "POST", suffix="/restore")
    assert restored.status_code == 200
    assert restored.json()["canvas"]["revision"] == 2 and restored.json()["document_revision"] == 0
    assert (
        restored.json()["canvas"]["status"] == "draft"
        and restored.json()["canvas"]["trashed_at"] is None
    )
    saved = snapshot(r)
    assert mutate(r, "POST", suffix="/restore").status_code == 200 and snapshot(r) == saved


def test_current_shelf_read_policy_blocks_writes_but_preserves_own_draft_recovery(draft):
    r = draft
    actions = {a: None for a in ACTIONS}
    actions["read_canvas"] = {
        "audience": "members",
        "min_grade_id": r.grades[2]["id"],
        "staff_only": False,
        "staff_bypass": False,
    }
    response = board_write(r, "PUT", f"/api/v1/shelves/{r.shelf_id}/policies", actions=actions)
    assert response.status_code == 200
    assert (
        r.client.get(f"/api/v1/shelves/{r.shelf_id}", headers=r.headers["member"]).status_code
        == 404
    )
    assert r.client.get(r.canvas_path + "/document", headers=r.headers["member"]).status_code == 200
    assert mutate(r, title="권한 회수").status_code == 403
    assert mutate(r, "DELETE").status_code == 204
    assert mutate(r, "POST", suffix="/restore").status_code == 403


@pytest.mark.parametrize("state", ["pending", "suspended", "banned", "board_suspended"])
def test_current_member_and_board_status_hide_own_drafts(draft, state):
    r = draft

    async def revoke():
        async with get_db() as db:
            if state == "board_suspended":
                (await db.get(Board, UUID(r.board["id"]))).status = "suspended"
            else:
                (await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))).status = state
            await db.commit()

    r.client.portal.call(revoke)
    before = snapshot(r)
    for method, suffix, body in [
        ("GET", "", None),
        ("GET", "/document", None),
        ("PATCH", "", {"expected_revision": 0, "title": "불가"}),
        ("DELETE", "", {"expected_revision": 0}),
        ("POST", "/restore", {"expected_revision": 0}),
    ]:
        response = r.client.request(
            method, r.canvas_path + suffix, headers=r.headers["member"], json=body
        )
        assert (
            response.status_code == 404 and response.json()["detail"]["error"] == "CANVAS_NOT_FOUND"
        )
    assert snapshot(r) == before


def test_archived_board_allows_author_read_and_hides_others_before_write_status(draft):
    r = draft
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert r.client.get(r.canvas_path, headers=r.headers["member"]).json()["capabilities"] == {
        "read_document": True,
        "edit_metadata": False,
        "trash": False,
        "restore": False,
    }
    assert r.client.get(r.canvas_path + "/document", headers=r.headers["member"]).status_code == 200
    assert mutate(r, title="보관 변경").status_code == 403
    assert mutate(r, "DELETE").status_code == 403
    assert mutate(r, "POST", suffix="/restore").status_code == 403
    assert create(r).status_code == 403
    assert (
        r.client.patch(
            r.canvas_path,
            headers=r.headers["owner"],
            json={"expected_revision": 0, "title": "타인 초안"},
        ).status_code
        == 404
    )


def test_membership_leave_and_rejoin_restore_only_own_low_grade_read(draft):
    r = draft
    assert r.client.delete(r.path + "/membership", headers=r.headers["member"]).status_code == 204
    assert r.client.get(r.canvas_path, headers=r.headers["member"]).status_code == 404
    assert r.client.post(r.path + "/join", headers=r.headers["member"]).status_code == 200
    own = r.client.get(r.canvas_path, headers=r.headers["member"])
    assert own.status_code == 200 and not own.json()["capabilities"]["edit_metadata"]


def test_atomic_same_board_move_and_both_shelf_policies(draft):
    r = draft
    destination = extra_shelf(r)
    actions = {a: None for a in ACTIONS}
    actions["create_canvas"] = {
        "audience": "members",
        "min_grade_id": r.grades[2]["id"],
        "staff_only": False,
        "staff_bypass": True,
    }
    assert (
        board_write(
            r, "PUT", f"/api/v1/shelves/{destination['id']}/policies", actions=actions
        ).status_code
        == 200
    )
    before = snapshot(r)
    assert mutate(r, title="부분 수정 금지", shelf_id=destination["id"]).status_code == 403
    assert snapshot(r) == before
    promote(r, grade=2)
    board_revision = revision(r)
    moved = mutate(r, title="이동한 초안", shelf_id=destination["id"])
    assert moved.status_code == 200 and moved.json()["canvas"]["shelf_id"] == destination["id"]
    assert moved.json()["canvas"]["revision"] == 1 and moved.json()["document_revision"] == 0
    assert revision(r) == board_revision
    other = r.client.post(
        "/api/v1/boards", headers=r.headers["owner"], json={**PAYLOAD, "slug": "foreign-canvas"}
    ).json()
    foreign_shelf = r.client.get(
        f"/api/v1/boards/{other['id']}/shelves", headers=r.headers["owner"]
    ).json()["items"][0]["id"]
    before = snapshot(r)
    assert mutate(r, shelf_id=foreign_shelf, title="타 보드 금지").status_code == 422
    assert create(r, shelf_id=foreign_shelf).status_code == 422
    assert snapshot(r) == before


def test_hidden_shelf_is_writable_and_notice_requires_current_operating_role(draft):
    r = draft
    assert (
        board_write(r, "PATCH", f"/api/v1/shelves/{r.shelf_id}", is_visible=False).status_code
        == 200
    )
    assert create(r).status_code == 201
    assert mutate(r, title="숨김은 권한 아님").status_code == 200
    notice = next(
        s
        for s in r.client.get(r.path + "/shelves", headers=r.headers["owner"]).json()["items"]
        if s["purpose"] == "notice"
    )
    promote(r, grade=2)
    assert create(r, shelf_id=notice["id"]).status_code == 403
    assert mutate(r, shelf_id=notice["id"]).status_code == 403
    created = create(r, actor="admin", shelf_id=notice["id"])
    assert created.status_code == 201
    assert r.client.get(created.headers["location"], headers=r.headers["owner"]).status_code == 404


def test_shelf_deletion_counts_draft_and_trash_until_atomic_move(draft):
    r = draft
    shelf = extra_shelf(r)
    assert mutate(r, shelf_id=shelf["id"]).status_code == 200
    shelf_path = f"/api/v1/shelves/{shelf['id']}"
    for trash in (False, True):
        if trash:
            assert mutate(r, "DELETE").status_code == 204
        rejected = board_write(r, "DELETE", shelf_path)
        assert (
            rejected.status_code == 409 and rejected.json()["detail"]["error"] == "SHELF_NOT_EMPTY"
        )
    assert mutate(r, "POST", suffix="/restore").status_code == 200
    assert mutate(r, shelf_id=r.shelf_id).status_code == 200
    assert board_write(r, "DELETE", shelf_path).status_code == 204
    assert r.client.get(r.canvas_path + "/document", headers=r.headers["member"]).status_code == 200


@pytest.mark.parametrize("days,expected", [(29, 200), (30, 409), (31, 409)])
def test_restoration_window_is_thirty_days_without_automatic_republication(draft, days, expected):
    r = draft
    assert mutate(r, "DELETE").status_code == 204
    now = datetime(2026, 10, 29, tzinfo=UTC)

    async def age():
        async with get_db() as db:
            canvas = await db.get(Canvas, UUID(r.canvas["canvas"]["id"]))
            canvas.trashed_at = now - timedelta(days=days)
            await db.commit()

    r.client.portal.call(age)
    with patch("app.services.canvas.utc_now", return_value=now):
        restored = mutate(r, "POST", suffix="/restore")
    assert restored.status_code == expected
    if expected == 409:
        assert restored.json()["detail"]["error"] == "CANVAS_RESTORE_EXPIRED"
    else:
        assert restored.json()["canvas"]["status"] == "draft"


@pytest.mark.parametrize("operation", ["create", "change", "trash", "restore"])
def test_commit_failure_rolls_back_metadata_and_document(operation, draft):
    r = draft
    if operation == "restore":
        assert mutate(r, "DELETE").status_code == 204
    before = snapshot(r)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        result = (
            create(r)
            if operation == "create"
            else mutate(r, "DELETE")
            if operation == "trash"
            else mutate(r, "POST", suffix="/restore")
            if operation == "restore"
            else mutate(r, title="롤백")
        )
    assert result.status_code == 503 and result.json()["detail"]["error"] == "CANVAS_UNAVAILABLE"
    assert snapshot(r) == before


def test_document_initialization_failure_does_not_leave_metadata(draft):
    r = draft
    before = snapshot(r)
    with patch(
        "app.models.canvas.CanvasDocument",
        side_effect=SQLAlchemyError("document initialization failed"),
    ):
        result = create(r)
    assert result.status_code == 503 and snapshot(r) == before


def test_account_deletion_anonymizes_author_without_exposing_or_removing_draft(draft):
    r = draft
    before = snapshot(r)

    async def remove():
        async with get_db() as db:
            email = (await db.get(User, r.ids["member"])).email
        await Users.delete_account(r.ids["member"], email)

    r.client.portal.call(remove)
    after = snapshot(r)
    assert after[1][0]["author_id"] is None and after[2] == before[2]
    for actor in ("owner", "admin", "peer"):
        assert (
            r.client.get(r.canvas_path + "/document", headers=r.headers[actor]).status_code == 404
        )


def test_active_empty_board_undo_rejects_draft_and_trash_and_archived_delete_cleans_both(
    integration_client,
):
    client = integration_client
    headers, owner_id = signup(client, "canvas-owner-cleanup")
    board = client.post("/api/v1/boards", headers=headers, json=PAYLOAD).json()
    path = f"/api/v1/boards/{board['id']}"
    home = client.get(path + "/home", headers=headers).json()
    shelf_id = next(s["id"] for s in home["shelves"] if s["is_default"])
    created = client.post(
        path + "/canvases", headers=headers, json={"shelf_id": shelf_id, "title": "단독 소유 초안"}
    )
    assert created.status_code == 201
    canvas_id = UUID(created.json()["canvas"]["id"])
    other_board = client.post(
        "/api/v1/boards", headers=headers, json={**PAYLOAD, "slug": "canvas-cleanup-other"}
    ).json()
    other_home = client.get(f"/api/v1/boards/{other_board['id']}/home", headers=headers).json()
    other_shelf = next(s["id"] for s in other_home["shelves"] if s["is_default"])
    other_canvas = client.post(
        f"/api/v1/boards/{other_board['id']}/canvases",
        headers=headers,
        json={"shelf_id": other_shelf, "title": "다른 보드의 초안"},
    )
    assert other_canvas.status_code == 201
    other_document = client.get(
        other_canvas.headers["location"] + "/document", headers=headers
    ).json()
    for trash in (False, True):
        if trash:
            assert (
                client.request(
                    "DELETE",
                    created.headers["location"],
                    headers=headers,
                    json={"expected_revision": 0},
                ).status_code
                == 204
            )
        assert (
            client.request(
                "DELETE",
                path,
                headers=headers,
                json={"expected_revision": 0, "confirm_slug": board["slug"]},
            ).status_code
            == 409
        )
    archived = client.patch(
        path, headers=headers, json={"expected_revision": 0, "reason": "종료", "status": "archived"}
    )
    assert archived.status_code == 200
    before = client.get(created.headers["location"], headers=headers).json()
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        assert (
            client.request(
                "DELETE",
                path,
                headers=headers,
                json={
                    "expected_revision": archived.json()["board_revision"],
                    "confirm_slug": board["slug"],
                },
            ).status_code
            == 503
        )
    assert client.get(created.headers["location"], headers=headers).json() == before
    assert (
        client.request(
            "DELETE",
            path,
            headers=headers,
            json={
                "expected_revision": archived.json()["board_revision"],
                "confirm_slug": board["slug"],
            },
        ).status_code
        == 204
    )

    async def check():
        async with get_db() as db:
            assert await db.get(Canvas, canvas_id) is None
            assert await db.get(CanvasDocument, canvas_id) is None
            assert await db.get(User, owner_id) is not None

    client.portal.call(check)
    assert (
        client.get(other_canvas.headers["location"] + "/document", headers=headers).json()
        == other_document
    )
