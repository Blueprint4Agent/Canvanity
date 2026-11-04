"""Shared SQLite/PostgreSQL feed scenarios: visibility, clocks, keysets and SQL shape."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, event, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.core.error.auth_exception import AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardMember,
    BoardMemberGrade,
    BoardPolicy,
    BoardRepository,
    Shelf,
    ShelfPolicy,
)
from app.models.canvas import (
    Canvas,
    CanvasContent,
    CanvasDocument,
    CanvasDocumentSaveForm,
    CanvasPatchForm,
    CanvasPublication,
    CanvasPublicationCounter,
    CanvasPublicationTag,
    CanvasPublishForm,
    CanvasRepository,
    CanvasRevisionForm,
    CanvasUnpublishForm,
)
from app.models.canvas_feed import CanvasFeedQuery, CanvasFeedRepository
from app.models.interest import Interest
from app.models.tag import CanvasTag, Tag
from app.models.user import User
from app.services.board import BoardService
from app.services.board_permission import BoardPermissionService
from app.services.canvas import CanvasService
from app.services.canvas_access import CanvasAccessService
from app.services.canvas_feed import CanvasFeedService
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import draft as draft, mutate
from tests.integration.api.v1.canvas.test_canvas_publication import publish

pytestmark = pytest.mark.primary_data
AT = datetime(2026, 11, 3, 11, 0, 0, 123456, tzinfo=UTC)


async def seed_feed(test_db):
    permissions = BoardPermissionService()
    boards = BoardService(permissions, BoardRepository())
    async with test_db() as db:
        owner, writer, reader, inactive = [
            User(
                email=f"feed-{name}@example.com",
                name=name,
                role="admin" if name == "reader" else "user",
                is_active=name != "inactive",
                is_verified=True,
            )
            for name in ("owner", "writer", "reader", "inactive")
        ]
        old, new = [Tag(name=name, normalized_name=name) for name in ("공개 태그", "초안 태그")]
        extras = [Tag(name=f"추가 태그 {n}", normalized_name=f"추가 태그 {n}") for n in (1, 2)]
        db.add_all([owner, writer, reader, inactive, old, new, *extras])
        await db.commit()
    created = []
    for index, (visibility, interests) in enumerate(
        (("public", ["ai"]), ("public", ["development"]), ("private", ["ai"]), ("public", ["ai"]))
    ):
        created.append(
            await boards.create(
                owner.id,
                BoardCreateForm(
                    name=f"피드 보드{index}",
                    slug=f"feed-board-{index}",
                    visibility=visibility,
                    join_policy="invite" if visibility == "private" else "open",
                    interest_ids=interests,
                ),
            )
        )
    shelves, grades = [], []
    async with test_db() as db:
        for board in created:
            shelves.append(
                (
                    await db.scalars(
                        select(Shelf).where(Shelf.board_id == board.id, Shelf.is_default.is_(True))
                    )
                ).one()
            )
            grades.append(
                list(
                    (
                        await db.scalars(
                            select(BoardMemberGrade)
                            .where(BoardMemberGrade.board_id == board.id)
                            .order_by(BoardMemberGrade.rank)
                        )
                    ).all()
                )
            )
            db.add(
                BoardMember(
                    board_id=board.id,
                    user_id=writer.id,
                    grade_id=grades[-1][1].id,
                    role="member",
                    status="active",
                )
            )
        db.add(
            BoardMember(
                board_id=created[0].id,
                user_id=reader.id,
                grade_id=grades[0][0].id,
                role="member",
                status="active",
            )
        )
        canvases = []
        # Higher IDs are intentionally inaccessible; they must never consume the page limit.
        for ident, index, live, snapshot, published, trashed in (
            (900, 0, "public", "public", True, False),
            (800, 1, "public", "public", True, False),
            (990, 0, "members", "public", True, False),
            (991, 0, "public", "members", True, False),
            (992, 2, "public", "public", True, False),
            (993, 3, "public", "public", True, False),
            (994, 0, "public", "public", False, False),
            (995, 0, "public", "public", True, True),
        ):
            canvas = Canvas(
                id=UUID(int=ident),
                board_id=created[index].id,
                shelf_id=shelves[index].id,
                author_id=writer.id,
                title="노출 금지 초안 제목",
                summary="노출 금지 초안 요약",
                visibility=live,
                revision=3,
                status="trashed" if trashed else "draft",
                trashed_at=AT if trashed else None,
            )
            db.add(canvas)
            await db.flush()
            db.add_all(
                [
                    CanvasDocument(
                        canvas_id=canvas.id,
                        document=CanvasContent().model_dump(mode="json"),
                        revision=2,
                    ),
                    CanvasPublicationCounter(canvas_id=canvas.id, revision=int(published)),
                    CanvasTag(canvas_id=canvas.id, tag_id=new.id),
                ]
            )
            if published:
                db.add(
                    CanvasPublication(
                        canvas_id=canvas.id,
                        publication_revision=1,
                        source_metadata_revision=1,
                        source_document_revision=1,
                        title=f"공개 제목 {ident}",
                        summary="공개 요약",
                        visibility=snapshot,
                        document=CanvasContent().model_dump(mode="json"),
                        published_at=AT,
                    )
                )
                if ident == 900:
                    db.add_all(
                        [
                            CanvasPublicationTag(
                                canvas_id=canvas.id, tag_id=tag.id, name=tag.name, position=n
                            )
                            for n, tag in enumerate(reversed(extras), 1)
                        ]
                    )
                await db.flush()
                db.add(
                    CanvasPublicationTag(
                        canvas_id=canvas.id, tag_id=old.id, name=old.name, position=0
                    )
                )
            canvases.append(canvas)
        (await db.get(Board, created[3].id)).status = "suspended"
        await db.commit()
    return SimpleNamespace(
        owner=owner,
        writer=writer,
        reader=reader,
        inactive=inactive,
        boards=created,
        shelves=shelves,
        grades=grades,
        canvases=canvases,
        old=old,
        new=new,
        extra_ids=[tag.id for tag in reversed(extras)],
        feed=CanvasFeedService(CanvasFeedRepository()),
        canvas=CanvasService(CanvasAccessService(permissions), CanvasRepository()),
    )


async def listing(r, user_id=None, **query):
    return await r.feed.list(user_id, CanvasFeedQuery(**query), scope="plaza")


def ids(response):
    return [item.canvas.id.int for item in response.items]


async def assert_feed_queries(test_db, r):
    first = await listing(r, limit=1)
    assert ids(first) == [900] and first.next_cursor
    assert (
        r.feed._before(first.next_cursor, "plaza", r.feed._filter_hash(CanvasFeedQuery()))[1].int
        == 900
    )
    second = await listing(r, limit=1, cursor=first.next_cursor)
    assert ids(second) == [800] and second.next_cursor is None
    assert ids(await listing(r, limit=100, cursor=first.next_cursor)) == [800]
    assert ids(await listing(r, interest_id="ai")) == [900]
    assert ids(await listing(r, interest_id="development", tag_id=r.old.id)) == [800]
    assert ids(await listing(r, tag_id=r.old.id)) == [900, 800]
    assert ids(await listing(r, tag_id=r.new.id)) == []
    assert ids(await listing(r, interest_id="missing-interest")) == []
    assert ids(await listing(r, tag_id=uuid4())) == []
    assert ids(await listing(r, r.reader.id)) == [991, 990, 900, 800]
    member_page = await listing(r, r.reader.id, limit=1)
    async with test_db() as db:
        (await db.get(BoardMember, (r.boards[0].id, r.reader.id))).status = "banned"
        await db.commit()
    assert ids(await listing(r, r.reader.id, limit=1, cursor=member_page.next_cursor)) == [800]
    async with test_db() as db:
        (await db.get(BoardMember, (r.boards[0].id, r.reader.id))).status = "active"
        interest = (await db.scalars(select(Interest).where(Interest.slug == "ai"))).one()
        interest.active = False
        await db.commit()
    assert ids(await listing(r, interest_id="ai")) == []
    async with test_db() as db:
        (await db.get(Interest, interest.id)).active = True
        await db.commit()
    assert ids(await listing(r, r.writer.id)) == [992, 991, 990, 900, 800]
    for ident in (r.inactive.id, 2**31 - 1):
        with pytest.raises(AuthException):
            await listing(r, ident)
    for query in (
        {"board_id": uuid4()},
        {"shelf_id": uuid4()},
        {"board_id": r.boards[2].id},
        {"shelf_id": r.shelves[2].id},
        {"board_id": r.boards[0].id, "shelf_id": r.shelves[1].id},
    ):
        with pytest.raises(CanvasException) as missing:
            await listing(r, **query)
        assert missing.value.code == CanvasErrorCode.NOT_FOUND.code
    assert ids(await listing(r, board_id=r.boards[0].id)) == [900]
    assert ids(await listing(r, shelf_id=r.shelves[1].id)) == [800]
    # Caller identities, scope and filter changes cannot turn a cursor into authorization.
    for query in (
        {"board_id": r.boards[0].id},
        {"shelf_id": r.shelves[0].id},
        {"tag_id": r.old.id},
        {"interest_id": "ai"},
    ):
        with pytest.raises(CanvasException) as changed:
            await listing(r, cursor=first.next_cursor, **query)
        assert changed.value.code == CanvasErrorCode.INVALID_CURSOR.code
    for item in (await listing(r)).items:
        assert item.canvas.title.startswith("공개 제목") and item.canvas.summary == "공개 요약"
        assert [tag.id for tag in item.canvas.tags] == [
            r.old.id,
            *(r.extra_ids if item.canvas.id.int == 900 else []),
        ]
        assert item.source_document_revision == item.source_metadata_revision == 1
        assert item.canvas.author_id == r.writer.id and item.shelf.id == item.canvas.shelf_id
        assert item.board.id == item.canvas.board_id
    async with test_db() as db:
        engine = db.bind
    statements = []

    def observed(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", observed)
    try:
        await listing(r, limit=100, interest_id="ai", tag_id=r.old.id)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", observed)
    assert len(statements) == 1
    assert (
        "canvas_publications.document" not in statements[0]
        and "canvas_documents" not in statements[0]
    )
    assert "canvas_tags" not in statements[0] and "canvas_publication_tags" in statements[0]


async def assert_feed_policy_parity(test_db, r):
    board_id, shelf_id, canvas_id = r.boards[0].id, r.shelves[0].id, r.canvases[0].id
    # Explicit meaningful branches, including grade bypass off and stricter Shelf overrides.
    cases = [
        ("public", "active", None, "member", 0, "public", False, True, "public", "public", True),
        ("private", "active", None, "member", 0, "public", False, True, "public", "public", False),
        (
            "public",
            "archived",
            "pending",
            "member",
            0,
            "public",
            False,
            True,
            "public",
            "public",
            True,
        ),
        (
            "public",
            "active",
            "pending",
            "member",
            2,
            "members",
            False,
            True,
            "public",
            "public",
            False,
        ),
        (
            "public",
            "active",
            "banned",
            "admin",
            2,
            "public",
            False,
            True,
            "public",
            "public",
            False,
        ),
        (
            "public",
            "active",
            "suspended",
            "moderator",
            2,
            "public",
            False,
            True,
            "public",
            "public",
            False,
        ),
        (
            "public",
            "suspended",
            "active",
            "admin",
            2,
            "public",
            False,
            True,
            "public",
            "public",
            False,
        ),
        (
            "private",
            "active",
            "active",
            "member",
            0,
            "public",
            False,
            True,
            "public",
            "public",
            True,
        ),
        ("public", "active", None, "member", 0, "public", False, True, "members", "public", False),
        ("public", "active", None, "member", 0, "public", False, True, "public", "members", False),
        (
            "public",
            "active",
            "active",
            "member",
            0,
            "public",
            False,
            True,
            "members",
            "members",
            True,
        ),
        (
            "public",
            "active",
            "active",
            "member",
            0,
            "members",
            False,
            True,
            "public",
            "public",
            False,
        ),
        (
            "public",
            "active",
            "active",
            "member",
            1,
            "members",
            False,
            True,
            "public",
            "public",
            True,
        ),
        (
            "public",
            "archived",
            "active",
            "member",
            2,
            "members",
            False,
            False,
            "members",
            "public",
            True,
        ),
        (
            "public",
            "active",
            "active",
            "moderator",
            0,
            "members",
            False,
            True,
            "public",
            "public",
            True,
        ),
        (
            "public",
            "active",
            "active",
            "admin",
            0,
            "members",
            False,
            False,
            "public",
            "public",
            False,
        ),
        (
            "public",
            "active",
            "active",
            "moderator",
            0,
            "members",
            True,
            False,
            "public",
            "public",
            True,
        ),
        (
            "public",
            "active",
            "active",
            "member",
            2,
            "members",
            True,
            True,
            "public",
            "public",
            False,
        ),
    ]
    for (
        visibility,
        status,
        member_status,
        role,
        grade,
        audience,
        staff_only,
        bypass,
        live,
        snapshot,
        expected,
    ) in cases:
        async with test_db() as db:
            board = await db.get(Board, board_id)
            board.visibility, board.join_policy, board.status = (
                visibility,
                "invite" if visibility == "private" else "open",
                status,
            )
            member = await db.get(BoardMember, (board_id, r.reader.id))
            if member is not None:
                await db.delete(member)
                await db.flush()
            if member_status is not None:
                db.add(
                    BoardMember(
                        board_id=board_id,
                        user_id=r.reader.id,
                        grade_id=r.grades[0][grade].id,
                        role=role,
                        status=member_status,
                    )
                )
            (await db.get(Canvas, canvas_id)).visibility = live
            (await db.get(CanvasPublication, canvas_id)).visibility = snapshot
            (await db.get(Shelf, shelf_id)).is_visible = False
            override = await db.get(ShelfPolicy, (board_id, shelf_id, "read_canvas"))
            if override is not None:
                await db.delete(override)
                await db.flush()
            db.add(
                ShelfPolicy(
                    board_id=board_id,
                    shelf_id=shelf_id,
                    action="read_canvas",
                    audience=audience,
                    staff_only=staff_only,
                    staff_bypass=bypass,
                    min_grade_id=r.grades[0][1].id
                    if audience == "members" and not staff_only
                    else None,
                )
            )
            await db.commit()
        actual = canvas_id in [item.canvas.id for item in (await listing(r, r.reader.id)).items]
        assert actual is expected, (
            visibility,
            status,
            member_status,
            role,
            grade,
            audience,
            staff_only,
            bypass,
            live,
            snapshot,
        )
        if expected:
            single = await r.canvas.get(r.reader.id, canvas_id, view="publication")
            scoped = await listing(r, r.reader.id, shelf_id=shelf_id)
            assert canvas_id in [item.canvas.id for item in scoped.items]
            assert single.canvas == next(
                item.canvas for item in scoped.items if item.canvas.id == canvas_id
            )
        else:
            with pytest.raises(CanvasException) as denied:
                await r.canvas.get(r.reader.id, canvas_id, view="publication")
            assert denied.value.code == CanvasErrorCode.NOT_FOUND.code
    async with test_db() as db:
        board = await db.get(Board, board_id)
        board.visibility, board.join_policy, board.status = "public", "open", "active"
        (await db.get(Canvas, canvas_id)).visibility = "public"
        (await db.get(CanvasPublication, canvas_id)).visibility = "public"
        await db.execute(
            delete(ShelfPolicy).where(
                ShelfPolicy.board_id == board_id, ShelfPolicy.shelf_id == shelf_id
            )
        )
        await db.execute(
            delete(BoardMember).where(
                BoardMember.board_id == board_id, BoardMember.user_id == r.reader.id
            )
        )
        await db.commit()
    assert canvas_id in [item.canvas.id for item in (await listing(r, r.reader.id)).items]
    # A Board can be readable while all its Shelf read policies deny this visitor.
    async with test_db() as db:
        policy = await db.get(BoardPolicy, (board_id, "read_canvas"))
        policy.audience, policy.min_grade_id = "members", r.grades[0][1].id
        await db.commit()
    assert ids(await listing(r, board_id=board_id)) == []
    with pytest.raises(CanvasException):
        await listing(r, shelf_id=shelf_id)
    async with test_db() as db:
        policy = await db.get(BoardPolicy, (board_id, "read_canvas"))
        policy.audience, policy.min_grade_id = "public", None
        await db.commit()


async def assert_feed_lifecycle(test_db, r):
    canvas_id = r.canvases[0].id
    first = await listing(r, limit=1)
    baseline = first.items[0]
    await r.canvas.change(
        r.writer.id,
        canvas_id,
        CanvasPatchForm(expected_revision=3, title="새 초안", tag_ids=[r.new.id]),
    )
    await r.canvas.save_document(
        r.writer.id,
        canvas_id,
        CanvasDocumentSaveForm(expected_revision=2, document=CanvasContent()),
    )
    assert (await listing(r, limit=1)).items[0] == baseline
    with patch("app.models.canvas.utc_now", return_value=AT + timedelta(seconds=1)):
        posted = await r.canvas.publish(
            r.writer.id,
            canvas_id,
            CanvasPublishForm(
                expected_metadata_revision=4,
                expected_document_revision=3,
                expected_publication_revision=1,
            ),
        )
    assert posted.publication_revision == 2
    assert ids(await listing(r, tag_id=r.old.id)) == [800]
    assert ids(await listing(r, tag_id=r.new.id)) == [900]
    # Another new publication appears before an existing cursor and does not duplicate lower items.
    new_id = r.canvases[6].id
    with patch("app.models.canvas.utc_now", return_value=AT + timedelta(seconds=2)):
        await r.canvas.publish(
            r.writer.id,
            new_id,
            CanvasPublishForm(
                expected_metadata_revision=3,
                expected_document_revision=2,
                expected_publication_revision=0,
            ),
        )
    assert ids(await listing(r)) == [994, 900, 800]
    assert ids(await listing(r, cursor=first.next_cursor)) == [800]
    # Live Shelf movement updates navigation and policy before the next republish.
    async with test_db() as db:
        notice = Shelf(
            board_id=r.boards[0].id,
            slug="projects",
            name="프로젝트",
            purpose="general",
            sort_order=2,
        )
        db.add(notice)
        await db.commit()
    await r.canvas.change(
        r.writer.id, canvas_id, CanvasPatchForm(expected_revision=4, shelf_id=notice.id)
    )
    moved = await listing(r, shelf_id=notice.id)
    assert ids(moved) == [900] and moved.items[0].shelf.slug == "projects"
    assert ids(await listing(r, shelf_id=r.shelves[0].id)) == [994]
    async with test_db() as db:
        db.add(
            ShelfPolicy(
                board_id=r.boards[0].id,
                shelf_id=notice.id,
                action="read_canvas",
                audience="members",
                min_grade_id=r.grades[0][1].id,
            )
        )
        await db.commit()
    with pytest.raises(CanvasException):
        await listing(r, shelf_id=notice.id)
    assert ids(await listing(r)) == [994, 800]
    async with test_db() as db:
        await db.execute(delete(ShelfPolicy).where(ShelfPolicy.shelf_id == notice.id))
        await db.commit()
    await r.canvas.unpublish(
        r.writer.id, canvas_id, CanvasUnpublishForm(expected_publication_revision=2)
    )
    assert ids(await listing(r, shelf_id=notice.id)) == []
    await r.canvas.trash(r.writer.id, new_id, CanvasRevisionForm(expected_revision=3))
    assert ids(await listing(r)) == [800]
    await r.canvas.restore(r.writer.id, new_id, CanvasRevisionForm(expected_revision=4))
    assert ids(await listing(r)) == [800]
    async with test_db() as db:
        writer = await db.get(User, r.writer.id)
        await db.delete(writer)
        await db.commit()
    remaining = (await listing(r)).items[0]
    assert remaining.canvas.id.int == 800 and remaining.canvas.author_id is None
    assert (
        await r.canvas.get(None, remaining.canvas.id, view="publication")
    ).canvas.author_id is None


def test_sqlite_feed_keysets_filters_current_policy_parity_and_lifecycle(integration_client):
    async def run():
        r = await seed_feed(get_db)
        await assert_feed_queries(get_db, r)
        await assert_feed_policy_parity(get_db, r)
        await assert_feed_lifecycle(get_db, r)

    integration_client.portal.call(run)


def test_feed_sql_failure_uses_canvas_domain_error(integration_client):
    async def run():
        with patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            side_effect=SQLAlchemyError("test-only failure"),
        ):
            with pytest.raises(CanvasException) as unavailable:
                await CanvasFeedRepository().read(None, CanvasFeedQuery(), None)
            assert unavailable.value.code == CanvasErrorCode.UNAVAILABLE.code

    integration_client.portal.call(run)


def test_feed_http_scope_optional_auth_api_key_and_inactive_bearer(draft):
    r = draft
    assert publish(r).status_code == 200
    paths = ["/api/v1/canvases", r.path + "/canvases", f"/api/v1/shelves/{r.shelf_id}/canvases"]
    key = r.client.post("/api/v1/api-keys", json={"name": "feed-read"}, headers=r.headers["member"])
    assert key.status_code == 200
    key_headers = {"X-API-Key": key.json()["api_key"]}
    assert r.client.get("/api/v1/auth/me", headers=key_headers).status_code == 200
    for path in paths:
        public = r.client.get(path)
        assert public.status_code == 200 and public.headers["cache-control"] == "private, no-store"
        assert public.json()["items"][0]["canvas"]["id"] == r.canvas["canvas"]["id"]
        assert r.client.get(path, headers=key_headers).json() == public.json()
    assert mutate(r, visibility="members").status_code == 200
    for path in paths:
        assert r.client.get(path, headers=key_headers).json() == {"items": [], "next_cursor": None}
        assert len(r.client.get(path, headers=r.headers["member"]).json()["items"]) == 1
        invalid = r.client.get(path, headers={**key_headers, "Authorization": "Bearer bad-token"})
        assert invalid.status_code == 401 and invalid.json()["detail"]["error"] == "INVALID_TOKEN"

    async def restrict_board_and_account():
        async with get_db() as db:
            board = await db.get(Board, UUID(r.board["id"]))
            board.visibility, board.join_policy = "private", "invite"
            (await db.get(User, r.ids["outsider"])).is_active = False
            await db.commit()

    r.client.portal.call(restrict_board_and_account)
    assert r.client.get(paths[0], headers=key_headers).json() == {"items": [], "next_cursor": None}
    for path in paths[1:]:
        denied = r.client.get(path, headers=key_headers)
        assert denied.status_code == 404 and denied.json()["detail"]["error"] == "CANVAS_NOT_FOUND"
        assert len(r.client.get(path, headers=r.headers["member"]).json()["items"]) == 1
    for path in paths:
        inactive = r.client.get(path, headers=r.headers["outsider"])
        assert (
            inactive.status_code == 404 and inactive.json()["detail"]["error"] == "USER_NOT_FOUND"
        )
