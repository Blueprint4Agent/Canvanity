"""Actual aggregate sources, UTC daily deduplication, retention and deletion."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.models.canvas import Canvas
from app.models.canvas_stats import CanvasView
from app.models.user import User
from app.services.canvas_stats import cleanup_canvas_views
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import draft as draft, snapshot
from tests.integration.api.v1.canvas.test_canvas_publication import publish, unpublish

pytestmark = pytest.mark.primary_data


def stats(r):
    return r.client.get(r.canvas_path + "/stats")


def view(r, actor="member"):
    return r.client.put(r.canvas_path + "/view", headers=r.headers[actor])


def rows(r):
    async def read():
        async with get_db() as db:
            return [
                (x.canvas_id, x.user_id, x.viewed_on)
                for x in (await db.scalars(select(CanvasView))).all()
            ]

    return r.client.portal.call(read)


def test_real_sources_daily_deduplication_state_changes_and_unchanged_clocks(draft):
    r = draft
    assert stats(r).status_code == view(r).status_code == 404
    assert publish(r).status_code == 200
    assert r.client.put(r.canvas_path + "/like", headers=r.headers["member"]).status_code == 200
    comment = r.client.post(
        r.canvas_path + "/comments", headers=r.headers["member"], json={"body": "실제 댓글"}
    )
    assert comment.status_code == 201
    at = datetime.now(UTC) + timedelta(seconds=1)
    before = snapshot(r)
    with patch("app.services.canvas_stats.utc_now", return_value=at):
        assert stats(r).json()["activity_score"] == 2 and rows(r) == []
        first = view(r).json()
        assert first["recorded"] and first["stats"]["view_count"] == 1
        assert not view(r).json()["recorded"]
        assert view(r, "outsider").json()["stats"]["view_count"] == 2
        assert stats(r).json()["activity_score"] == 4
    with patch("app.services.canvas_stats.utc_now", return_value=at + timedelta(days=1)):
        assert view(r).json()["stats"]["view_count"] == 3
        assert stats(r).json()["window_started_on"] == (at.date() - timedelta(days=28)).isoformat()
        assert (
            r.client.patch(
                comment.headers["location"],
                headers=r.headers["owner"],
                json={"expected_revision": 0, "status": "hidden", "reason": "검토"},
            ).status_code
            == 200
        )
        assert stats(r).json()["comment_count"] == 0 and stats(r).json()["activity_score"] == 4
        assert (
            r.client.delete(r.canvas_path + "/like", headers=r.headers["member"]).status_code == 200
        )
        assert stats(r).json()["like_count"] == 0 and stats(r).json()["activity_score"] == 3
    assert snapshot(r) == before
    assert unpublish(r).status_code == 200
    assert stats(r).status_code == view(r).status_code == 404
    assert len(rows(r)) == 3


def test_window_boundary_bounded_cleanup_rollback_and_cascades(draft):
    r = draft
    assert publish(r).status_code == 200
    at = datetime.now(UTC)
    cid = UUID(r.canvas["canvas"]["id"])

    async def seed():
        async with get_db() as db:
            for actor, offset in [("member", 31), ("peer", 30), ("member", 29), ("peer", -1)]:
                db.add(
                    CanvasView(
                        canvas_id=cid,
                        user_id=r.ids[actor],
                        viewed_on=at.date() - timedelta(days=offset),
                    )
                )
            await db.commit()

    r.client.portal.call(seed)
    with patch("app.services.canvas_stats.utc_now", return_value=at):
        assert stats(r).json()["view_count"] == 1
        assert r.client.portal.call(lambda: cleanup_canvas_views(at=at, limit=1)) == 1
        assert r.client.portal.call(lambda: cleanup_canvas_views(at=at, limit=1)) == 1
        assert r.client.portal.call(lambda: cleanup_canvas_views(at=at, limit=1)) == 0
        assert len(rows(r)) == 2
        with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("failed commit")):
            assert view(r, "outsider").status_code == 503
        assert len(rows(r)) == 2
        assert view(r).json()["stats"]["view_count"] == 2

        async def remove_user():
            async with get_db() as db:
                await db.execute(delete(User).where(User.id == r.ids["member"]))
                await db.commit()

        r.client.portal.call(remove_user)
        assert stats(r).json()["view_count"] == 0 and len(rows(r)) == 1

    async def remove_canvas():
        async with get_db() as db:
            await db.execute(delete(Canvas).where(Canvas.id == cid))
            await db.commit()

    r.client.portal.call(remove_canvas)
    assert rows(r) == []
