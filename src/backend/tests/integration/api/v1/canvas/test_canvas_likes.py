"""Real HTTP/SQLite reaction lifecycle, permission and atomicity checks."""

from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.models.canvas import Canvas, CanvasLike
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import (
    board_write,
    draft as draft,
    mutate,
    snapshot,
)
from tests.integration.api.v1.canvas.test_canvas_publication import publish, unpublish

pytestmark = pytest.mark.primary_data


def like(r, method="PUT", actor="member"):
    return r.client.request(
        method, r.canvas_path + "/like", headers=r.headers[actor] if actor else {}
    )


def rows(r):
    async def read():
        async with get_db() as db:
            return [
                (row.canvas_id, row.user_id, row.created_at)
                for row in (await db.scalars(select(CanvasLike))).all()
            ]

    return r.client.portal.call(read)


def test_idempotence_individual_state_and_unchanged_content_clocks(draft):
    r = draft
    assert like(r).status_code == 404  # Even the author cannot react to an unpublished draft.
    assert publish(r).status_code == 200
    before = snapshot(r)
    for _ in range(2):
        result = like(r)
        assert result.status_code == 200, result.text
        assert result.json() == {"count": 1, "liked": True}
    saved = rows(r)
    assert like(r).status_code == 200 and rows(r) == saved
    assert like(r, actor="peer").json() == {"count": 2, "liked": True}
    assert like(r, "GET", None).json() == {"count": 2, "liked": False}
    assert like(r, "GET").json() == {"count": 2, "liked": True}
    for _ in range(2):
        assert like(r, "DELETE").json() == {"count": 1, "liked": False}
    assert snapshot(r) == before
    assert len(rows(r)) == 1


def test_unpublish_trash_and_republish_preserve_but_conceal_reactions(draft):
    r = draft
    assert publish(r).status_code == 200
    assert like(r).status_code == 200
    saved = rows(r)
    assert unpublish(r).status_code == 200
    for method in ("GET", "PUT", "DELETE"):
        assert like(r, method).status_code == 404
    assert rows(r) == saved
    assert publish(r).status_code == 200
    assert like(r, "GET").json() == {"count": 1, "liked": True}
    assert mutate(r, "DELETE").status_code == 204
    assert like(r, "GET", None).status_code == 404 and rows(r) == saved


def test_current_react_policy_archive_and_member_sanctions(draft):
    r = draft
    assert publish(r).status_code == 200
    assert like(r, actor="outsider").status_code == 403
    assert like(r).status_code == 200
    policy = r.client.get(r.path + "/policies", headers=r.headers["owner"]).json()["actions"]
    policy["react"]["staff_only"] = True
    policy["react"]["min_grade_id"] = None
    assert board_write(r, "PUT", r.path + "/policies", actions=policy).status_code == 200
    assert like(r).status_code == like(r, "DELETE").status_code == 403
    assert like(r, "GET").json() == {"count": 1, "liked": True}
    assert like(r, actor="admin").status_code == 200
    assert (
        board_write(r, "PATCH", r.path + f"/members/{r.ids['member']}", status="banned").status_code
        == 200
    )
    for method in ("GET", "PUT", "DELETE"):
        assert like(r, method).status_code == 404
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert like(r, "GET", None).status_code == 200
    assert like(r, actor="admin").status_code == 403


def test_commit_failure_rolls_back_and_canvas_delete_cascades(draft):
    r = draft
    assert publish(r).status_code == 200
    before = rows(r)
    with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("commit failed")):
        assert like(r).status_code == 503
    assert rows(r) == before
    assert like(r).status_code == 200

    async def remove():
        async with get_db() as db:
            await db.execute(delete(Canvas).where(Canvas.id == UUID(r.canvas["canvas"]["id"])))
            await db.commit()

    r.client.portal.call(remove)
    assert rows(r) == []
