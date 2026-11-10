"""Actual membership-independent selection, feed and current-policy lifecycle."""

from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.models.board import BoardSubscription
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import board_write, draft as draft
from tests.integration.api.v1.canvas.test_canvas_publication import publish, unpublish

pytestmark = pytest.mark.primary_data
FEED = "/api/v1/me/subscriptions/canvases"


def subscription(r, method="GET", actor="outsider"):
    return r.client.request(method, r.path + "/subscription", headers=r.headers[actor])


def selected(r, actor="outsider", **query):
    return r.client.get(FEED, headers=r.headers[actor], params=query)


def rows(r):
    async def read():
        async with get_db() as db:
            return [
                (x.board_id, x.user_id, x.created_at)
                for x in (await db.scalars(select(BoardSubscription))).all()
            ]

    return r.client.portal.call(read)


def test_idempotence_membership_independence_current_private_and_archive(draft):
    r = draft
    assert publish(r).status_code == 200
    before = r.client.get(r.path + "/home", headers=r.headers["owner"]).json()["board"]["revision"]
    assert selected(r).json()["items"] == []
    assert subscription(r).json() == {"subscribed": False}
    assert subscription(r, "PUT").json() == {"subscribed": True}
    saved = rows(r)
    assert subscription(r, "PUT").status_code == 200 and rows(r) == saved
    assert len(selected(r).json()["items"]) == 1
    home = r.client.get(r.path + "/home", headers=r.headers["outsider"]).json()
    assert home["membership"] is None and home["board"]["revision"] == before
    assert r.client.post(r.path + "/join", headers=r.headers["outsider"]).status_code == 200
    assert r.client.delete(r.path + "/membership", headers=r.headers["outsider"]).status_code == 204
    assert subscription(r).json()["subscribed"] and rows(r) == saved
    assert (
        board_write(r, "PATCH", r.path, visibility="private", join_policy="invite").status_code
        == 200
    )
    assert selected(r).json()["items"] == []
    assert subscription(r).status_code == 404
    assert (
        board_write(r, "PATCH", r.path, visibility="public", join_policy="open").status_code == 200
    )
    assert subscription(r).json()["subscribed"]
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert subscription(r, "PUT").status_code == 403
    assert subscription(r, "DELETE").json() == {"subscribed": False}
    assert subscription(r, "DELETE").json() == {"subscribed": False}
    assert selected(r).json()["items"] == []


def test_rollback_current_sanctions_unpublish_and_cursor_scope(draft):
    r = draft
    assert publish(r).status_code == 200
    with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("failed commit")):
        assert subscription(r, "PUT", actor="peer").status_code == 503
    assert subscription(r, actor="peer").json() == {"subscribed": False}
    assert subscription(r, "PUT", actor="peer").status_code == 200
    assert len(selected(r, actor="peer").json()["items"]) == 1
    assert (
        board_write(r, "PATCH", r.path + f"/members/{r.ids['peer']}", status="banned").status_code
        == 200
    )
    assert selected(r, actor="peer").json()["items"] == []
    assert subscription(r, actor="peer").status_code == 404
    assert subscription(r, "PUT").status_code == 200
    assert unpublish(r).status_code == 200
    assert selected(r).json()["items"] == []
