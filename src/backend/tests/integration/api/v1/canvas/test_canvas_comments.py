"""Actual comment ownership, moderation, lifecycle, pagination and rollback."""

from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.models.canvas_comment import CanvasComment
from app.models.user import User
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import board_write, draft as draft, snapshot
from tests.integration.api.v1.canvas.test_canvas_publication import publish, unpublish

pytestmark = pytest.mark.primary_data


def create(r, body="첫 댓글", actor="member"):
    return r.client.post(r.canvas_path + "/comments", headers=r.headers[actor], json={"body": body})


def change(r, path, *, actor="member", method="PATCH", revision=0, **body):
    return r.client.request(
        method, path, headers=r.headers[actor], json={"expected_revision": revision, **body}
    )


def test_owner_cas_moderation_hidden_body_and_idempotent_delete(draft):
    r = draft
    assert create(r).status_code == 404
    assert publish(r).status_code == 200
    before = snapshot(r)
    created = create(r)
    assert created.status_code == 201, created.text
    path = created.headers["location"]
    assert change(r, path, actor="peer", body="다른 사람").status_code == 403
    assert change(r, path, actor="owner", body="운영자가 타인 편집").status_code == 403
    assert change(r, path, body="첫 댓글").json()["revision"] == 0
    assert change(r, path, body="수정 댓글").json()["revision"] == 1
    assert change(r, path, body="오래된 수정").status_code == 409
    hidden = change(r, path, actor="moderator", revision=1, status="hidden", reason="운영 숨김")
    assert hidden.status_code == 200 and hidden.json()["revision"] == 2
    assert r.client.get(path).status_code == 404
    assert r.client.get(path, headers=r.headers["peer"]).status_code == 404
    own = r.client.get(path, headers=r.headers["member"])
    assert own.status_code == 200 and not own.json()["capabilities"]["edit"]
    assert r.client.get(r.canvas_path + "/comments").json()["items"] == []
    assert (
        r.client.get(
            r.canvas_path + "/comments", params={"status": "all"}, headers=r.headers["member"]
        ).status_code
        == 403
    )
    assert (
        len(
            r.client.get(
                r.canvas_path + "/comments",
                params={"status": "all"},
                headers=r.headers["moderator"],
            ).json()["items"]
        )
        == 1
    )
    assert change(r, path, revision=2, status="visible", reason="내 복원").status_code == 403
    assert (
        change(r, path, actor="owner", revision=2, status="visible", reason="운영 복원").json()[
            "revision"
        ]
        == 3
    )
    deleted = change(r, path, method="DELETE", revision=3)
    assert deleted.json()["body"] is None and deleted.json()["status"] == "deleted"
    assert change(r, path, method="DELETE", revision=4).json() == deleted.json()
    assert (
        change(r, path, actor="owner", revision=4, status="visible", reason="삭제 복원").status_code
        == 403
    )
    assert snapshot(r) == before


def test_pagination_current_permissions_lifecycle_and_failed_commit(draft):
    r = draft
    assert publish(r).status_code == 200
    paths = [create(r, str(i)).headers["location"] for i in range(3)]
    endpoint = r.canvas_path + "/comments"
    first = r.client.get(endpoint, params={"limit": 2}).json()
    second = r.client.get(endpoint, params={"limit": 2, "cursor": first["next_cursor"]}).json()
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert len({x["id"] for x in first["items"] + second["items"]}) == 3
    assert (
        r.client.get(
            endpoint, params={"cursor": first["next_cursor"]}, headers=r.headers["member"]
        ).status_code
        == 422
    )
    assert r.client.get(endpoint, params={"cursor": "wrong"}).status_code == 422
    with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("failed commit")):
        assert change(r, paths[0], body="rollback").status_code == 503
    assert r.client.get(paths[0]).json()["body"] == "0"
    assert (
        board_write(r, "PATCH", r.path + f"/members/{r.ids['member']}", status="banned").status_code
        == 200
    )
    assert r.client.get(endpoint, headers=r.headers["member"]).status_code == 404
    assert create(r).status_code == 404
    assert (
        board_write(r, "PATCH", r.path + f"/members/{r.ids['member']}", status="active").status_code
        == 200
    )
    assert unpublish(r).status_code == 200
    assert r.client.get(paths[0]).status_code == create(r).status_code == 404


def test_hidden_orphan_is_not_public_and_account_delete_preserves_comment(draft):
    r = draft
    assert publish(r).status_code == 200
    created = create(r)
    path = created.headers["location"]
    assert change(r, path, actor="owner", status="hidden", reason="검토").status_code == 200

    async def remove():
        async with get_db() as db:
            await db.execute(delete(User).where(User.id == r.ids["member"]))
            await db.commit()
            row = await db.scalar(
                select(CanvasComment).where(CanvasComment.id == UUID(created.json()["id"]))
            )
            assert row.author_id is None and row.body == "첫 댓글"

    r.client.portal.call(remove)
    assert r.client.get(path).status_code == 404
    assert r.client.get(path, headers=r.headers["owner"]).json()["author_id"] is None
