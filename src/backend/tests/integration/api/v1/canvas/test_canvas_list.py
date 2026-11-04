"""Owner listing on real SQL: current policy, clocks, expiry, pagination and bounded reads."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, event, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import Base, get_db
from app.core.error.auth_exception import AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import Board, BoardMember, BoardPolicy, Shelf, ShelfPolicy
from app.models.canvas import (
    Canvas,
    CanvasContent,
    CanvasCreateForm,
    CanvasDocument,
    CanvasDocumentSaveForm,
    CanvasPatchForm,
    CanvasPublication,
    CanvasPublicationCounter,
    CanvasPublishForm,
    CanvasRevisionForm,
    CanvasUnpublishForm,
)
from app.models.canvas_list import CanvasListQuery, CanvasListRepository
from app.models.user import User
from app.services.canvas_list import CanvasListService
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import draft as draft
from tests.integration.api.v1.canvas.test_canvas_feed import ids, seed_feed

pytestmark = pytest.mark.primary_data
AT = datetime(2026, 11, 4, 0, 0, 0, 123456, tzinfo=UTC)


async def seed_list(test_db):
    r = await seed_feed(test_db)
    r.list = CanvasListService(r.canvas.access, CanvasListRepository())
    async with test_db() as db:
        for canvas in await db.scalars(select(Canvas)):
            canvas.updated_at = AT
            canvas.created_at = AT - timedelta(days=1)
        for document in await db.scalars(select(CanvasDocument)):
            document.updated_at = AT
        # Real trash never retains a publication; state counter persists after its removal.
        await db.execute(
            delete(CanvasPublication).where(CanvasPublication.canvas_id == UUID(int=995))
        )
        (await db.get(CanvasPublicationCounter, UUID(int=995))).revision = 2
        (await db.get(Canvas, UUID(int=995))).trashed_at = AT - timedelta(days=1)
        await db.commit()
    return r


async def listing(r, user_id=None, **query):
    return await r.list.list(r.writer.id if user_id is None else user_id, CanvasListQuery(**query))


async def assert_parity(r, response):
    for item in response.items:
        with patch("app.services.canvas.utc_now", return_value=response.as_of):
            single = await r.canvas.get(r.writer.id, item.canvas.id, view="draft")
        assert item.model_dump(include=set(type(single).model_fields)) == single.model_dump()
        assert item.last_modified_at == max(item.canvas.updated_at, item.document_updated_at)


async def assert_queries(test_db, r):
    response = await listing(r)
    assert ids(response) == [994, 992, 991, 990, 900, 800]
    assert response.next_cursor is None
    await assert_parity(r, response)
    assert ids(await listing(r, status="all")) == [995, 994, 992, 991, 990, 900, 800]
    assert ids(await listing(r, status="trashed")) == [995]
    assert ids(await listing(r, publication="unpublished")) == [994]
    assert ids(await listing(r, publication="published")) == [992, 991, 990, 900, 800]
    assert ids(await listing(r, status="trashed", publication="published")) == []
    assert ids(await listing(r, status="all", publication="unpublished")) == [995, 994]
    assert ids(await listing(r, board_id=r.boards[2].id)) == [992]  # private Board, active author
    assert ids(await listing(r, shelf_id=r.shelves[1].id)) == [800]
    async with test_db() as db:
        empty = Shelf(
            board_id=r.boards[0].id,
            slug="empty-scope",
            name="범위 검사 분류",
            purpose="general",
            sort_order=10,
            is_visible=False,
        )
        db.add(empty)
        await db.commit()
    # Hidden menu is not ACL; readable empty scope is legitimate, unlike denied/no-own.
    assert ids(await listing(r, shelf_id=empty.id)) == []
    async with test_db() as db:
        for shelf_id in (empty.id, r.shelves[0].id):
            db.add(
                ShelfPolicy(
                    board_id=r.boards[0].id,
                    shelf_id=shelf_id,
                    action="read_canvas",
                    audience="members",
                    min_grade_id=r.grades[0][2].id,
                )
            )
        await db.commit()
    for scope in (
        {"shelf_id": empty.id},
        {"shelf_id": uuid4()},
        {"board_id": r.boards[1].id, "shelf_id": empty.id},
    ):
        with pytest.raises(CanvasException) as denied:
            await listing(r, **scope)
        assert denied.value.code == CanvasErrorCode.NOT_FOUND.code
    owned = await listing(r, shelf_id=r.shelves[0].id)
    assert ids(owned) == [994, 991, 990, 900]
    await assert_parity(r, owned)
    # Own existence ignores both lifecycle and publication filters, even for an empty result.
    assert (
        ids(await listing(r, shelf_id=r.shelves[0].id, status="trashed", publication="published"))
        == []
    )
    async with test_db() as db:
        await db.execute(
            delete(ShelfPolicy).where(ShelfPolicy.shelf_id.in_((empty.id, r.shelves[0].id)))
        )
        await db.delete(await db.get(Shelf, empty.id))
        await db.commit()
    first = await listing(r, limit=2)
    second = await listing(r, limit=1, cursor=first.next_cursor)
    third = await listing(r, limit=100, cursor=second.next_cursor)
    assert ids(first) == [994, 992] and ids(second) == [991] and ids(third) == [990, 900, 800]
    assert third.next_cursor is None
    assert ids(await listing(r, r.owner.id)) == []  # role/Board ownership is not authorship
    assert ids(await listing(r, r.reader.id)) == []  # app-wide admin is not authorship
    assert ids(await listing(r, r.owner.id, board_id=r.boards[0].id)) == []
    for user_id in (r.reader.id, r.owner.id):
        with pytest.raises(CanvasException):
            await listing(r, user_id, cursor=first.next_cursor)
    for user_id in (r.inactive.id, 2**31 - 1):
        with pytest.raises(AuthException):
            await listing(r, user_id)
    for query in (
        {"board_id": uuid4()},
        {"shelf_id": uuid4()},
        {"board_id": r.boards[3].id},
        {"shelf_id": r.shelves[3].id},
        {"board_id": r.boards[0].id, "shelf_id": r.shelves[1].id},
    ):
        with pytest.raises(CanvasException) as missing:
            await listing(r, **query)
        assert missing.value.code == CanvasErrorCode.NOT_FOUND.code
    for item in response.items:
        assert item.canvas.title == "노출 금지 초안 제목"
        assert [tag.id for tag in item.canvas.tags] == [r.new.id]
        assert item.document_revision == 2 and item.canvas.revision == 3
        assert item.last_modified_at == AT and item.trash_expires_at is None
        assert item.trash_expired is False
        assert set(item.model_dump()) == {
            "canvas",
            "document_revision",
            "view",
            "capabilities",
            "publication_revision",
            "publication",
            "document_updated_at",
            "last_modified_at",
            "trash_expires_at",
            "trash_expired",
        }
    async with test_db() as db:
        engine = db.bind
        assert (
            await db.scalar(select(Canvas.author_id).where(Canvas.id == UUID(int=900)))
            == r.writer.id
        )
    statements = []

    def observed(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", observed)
    try:
        await listing(r, limit=1)
        small = list(statements)
        statements.clear()
        await listing(r, limit=100)
        large = list(statements)
        statements.clear()
        await listing(r, shelf_id=r.shelves[0].id, limit=100)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", observed)
    assert len(small) == len(large) == 6 and len(statements) == 7
    for sql in [*small, *large, *statements]:
        assert "canvas_documents.document" not in sql and "canvas_publications.document" not in sql
        assert "count(" not in sql.lower()


async def assert_policy(test_db, r):
    async def update(model, key, **changes):
        async with test_db() as db:
            row = await db.get(model, key)
            for name, value in changes.items():
                setattr(row, name, value)
            await db.commit()

    board_id = r.boards[0].id
    member_key = (board_id, r.writer.id)
    cursor = (await listing(r, limit=1)).next_cursor
    for status in ("pending", "banned", "suspended"):
        await update(BoardMember, member_key, status=status)
        assert ids(await listing(r, limit=1)) == [992]
        assert ids(await listing(r, cursor=cursor)) == [992, 800]
        for scope in ({"board_id": board_id}, {"shelf_id": r.shelves[0].id}):
            with pytest.raises(CanvasException):
                await listing(r, **scope)
        with pytest.raises(CanvasException):
            await r.canvas.get(r.writer.id, UUID(int=900), view="draft")
    await update(BoardMember, member_key, status="active")
    async with test_db() as db:
        for action in ("read_canvas", "create_canvas"):
            db.add(
                ShelfPolicy(
                    board_id=board_id,
                    shelf_id=r.shelves[0].id,
                    action=action,
                    audience="members",
                    min_grade_id=r.grades[0][2].id,
                    staff_bypass=False,
                )
            )
        await db.commit()
    overridden = await listing(r, shelf_id=r.shelves[0].id)
    assert ids(overridden) == [994, 991, 990, 900]
    assert all(not item.capabilities.edit_document for item in overridden.items)
    await assert_parity(r, overridden)
    async with test_db() as db:
        await db.execute(delete(ShelfPolicy).where(ShelfPolicy.shelf_id == r.shelves[0].id))
        await db.commit()
    for action in ("read_canvas", "create_canvas"):
        await update(
            BoardPolicy, (board_id, action), audience="members", min_grade_id=r.grades[0][2].id
        )
    # Hidden menu/low read grade does not conceal one's own draft or leak Shelf names.
    await update(Shelf, r.shelves[0].id, is_visible=False)
    low = await listing(r, board_id=board_id)
    assert ids(low) == [994, 991, 990, 900]
    await assert_parity(r, low)
    for item in low.items:
        assert not item.capabilities.edit_document and not item.capabilities.publish
        assert item.capabilities.trash
        assert item.capabilities.unpublish == (item.publication is not None)
    await update(BoardMember, member_key, role="moderator")
    staff = await listing(r, board_id=board_id)
    assert all(item.capabilities.edit_document for item in staff.items)
    await assert_parity(r, staff)
    await update(Board, board_id, status="archived")
    archived = await listing(r, board_id=board_id, status="all")
    await assert_parity(r, archived)
    assert all(
        not any(
            (
                item.capabilities.edit_document,
                item.capabilities.restore,
                item.capabilities.trash,
                item.capabilities.publish,
                item.capabilities.unpublish,
            )
        )
        for item in archived.items
    )
    await update(Board, board_id, status="suspended")
    assert 900 not in ids(await listing(r))
    await update(Board, board_id, status="active")
    await update(BoardMember, member_key, role="member", grade_id=r.grades[0][2].id)
    # Public Board after membership deletion still cannot reveal the author's draft.
    async with test_db() as db:
        member = await db.get(BoardMember, member_key)
        await db.delete(member)
        await db.commit()
    assert 900 not in ids(await listing(r))
    with pytest.raises(CanvasException):
        await listing(r, board_id=board_id)
    async with test_db() as db:
        db.add(
            BoardMember(
                board_id=board_id,
                user_id=r.writer.id,
                role="member",
                status="active",
                grade_id=r.grades[0][1].id,
            )
        )
        for action in ("read_canvas", "create_canvas"):
            policy = await db.get(BoardPolicy, (board_id, action))
            policy.audience = "members"
            policy.min_grade_id = r.grades[0][0 if action == "read_canvas" else 1].id
        await db.commit()
    await update(User, r.writer.id, is_active=False)
    with pytest.raises(AuthException):
        await listing(r)
    await update(User, r.writer.id, is_active=True)


async def assert_lifecycle(test_db, r):
    created = await r.canvas.create(
        r.writer.id,
        r.boards[0].id,
        CanvasCreateForm(shelf_id=r.shelves[0].id, title="생성", tag_ids=[r.old.id]),
    )
    canvas_id = created.canvas.id
    async with test_db() as db:
        (await db.get(Canvas, canvas_id)).updated_at = AT - timedelta(seconds=2)
        (await db.get(CanvasDocument, canvas_id)).updated_at = AT - timedelta(seconds=2)
        await db.commit()
    cursor = (await listing(r, limit=2)).next_cursor
    with patch("app.models.canvas.utc_now", return_value=AT + timedelta(seconds=1)):
        await r.canvas.save_document(
            r.writer.id,
            canvas_id,
            CanvasDocumentSaveForm(expected_revision=0, document=CanvasContent()),
        )
    newest = (await listing(r)).items[0]
    assert (
        newest.canvas.id == canvas_id
        and newest.document_revision == 1
        and newest.canvas.revision == 0
    )
    assert newest.last_modified_at == AT + timedelta(seconds=1)
    assert canvas_id not in [item.canvas.id for item in (await listing(r, cursor=cursor)).items]
    with patch("app.models.canvas.utc_now", return_value=AT + timedelta(seconds=2)):
        await r.canvas.change(
            r.writer.id,
            canvas_id,
            CanvasPatchForm(expected_revision=0, title="최신 초안", tag_ids=[r.new.id]),
        )
    changed = (await listing(r)).items[0]
    assert changed.canvas.revision == 1 and changed.document_revision == 1
    assert changed.last_modified_at == AT + timedelta(seconds=2)
    await r.canvas.publish(
        r.writer.id,
        canvas_id,
        CanvasPublishForm(
            expected_metadata_revision=1,
            expected_document_revision=1,
            expected_publication_revision=0,
        ),
    )
    posted = (await listing(r)).items[0]
    assert posted.last_modified_at == changed.last_modified_at and posted.publication_revision == 1
    await r.canvas.unpublish(
        r.writer.id, canvas_id, CanvasUnpublishForm(expected_publication_revision=1)
    )
    assert (await listing(r)).items[0].last_modified_at == changed.last_modified_at
    await r.canvas.trash(r.writer.id, canvas_id, CanvasRevisionForm(expected_revision=1))
    assert canvas_id not in [item.canvas.id for item in (await listing(r)).items]
    for delta, expired in (
        (timedelta(microseconds=-1), False),
        (timedelta(), True),
        (timedelta(microseconds=1), True),
    ):
        async with test_db() as db:
            (await db.get(Canvas, canvas_id)).trashed_at = AT - timedelta(days=30)
            await db.commit()
        with patch("app.services.canvas_list.utc_now", return_value=AT + delta):
            trash = await listing(r, status="trashed")
        item = next(item for item in trash.items if item.canvas.id == canvas_id)
        assert item.trash_expires_at == AT and item.trash_expired is expired
        assert item.capabilities.restore is not expired
        await assert_parity(r, trash)
    with patch("app.services.canvas.utc_now", return_value=AT - timedelta(microseconds=1)):
        await r.canvas.restore(r.writer.id, canvas_id, CanvasRevisionForm(expected_revision=2))
    restored = next(item for item in (await listing(r)).items if item.canvas.id == canvas_id)
    assert restored.publication is None and restored.publication_revision == 2
    assert restored.canvas.status == "draft" and restored.trash_expires_at is None


async def state(test_db):
    async with test_db() as db:
        return {
            table.name: [dict(row) for row in (await db.execute(select(table))).mappings()]
            for table in Base.metadata.sorted_tables
        }


def test_sqlite_owner_queries_policy_lifecycle_and_read_only_state(integration_client):
    async def run():
        r = await seed_list(get_db)
        await assert_queries(get_db, r)
        await assert_policy(get_db, r)
        await assert_lifecycle(get_db, r)
        before = await state(get_db)
        await listing(r, status="all")
        assert await state(get_db) == before

    integration_client.portal.call(run)


def test_missing_document_and_sql_failure_are_503_without_silently_hiding_rows(integration_client):
    async def run():
        r = await seed_list(get_db)
        async with get_db() as db:
            await db.execute(
                delete(CanvasDocument).where(CanvasDocument.canvas_id == UUID(int=994))
            )
            await db.commit()
        with pytest.raises(CanvasException) as missing:
            await listing(r)
        assert missing.value.code == CanvasErrorCode.UNAVAILABLE.code
        with patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            side_effect=SQLAlchemyError("test failure"),
        ):
            with pytest.raises(CanvasException) as failure:
                await listing(r)
        assert failure.value.code == CanvasErrorCode.UNAVAILABLE.code
        assert isinstance(failure.value.__cause__, SQLAlchemyError)

    integration_client.portal.call(run)


def test_owner_list_real_http_current_auth_and_scope(draft):
    r = draft
    response = r.client.get("/api/v1/me/canvases", headers=r.headers["member"])
    assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
    assert response.json()["items"][0]["canvas"] == r.canvas["canvas"]
    assert (
        response.json()["items"][0]["capabilities"]
        == r.client.get(r.canvas_path, headers=r.headers["member"]).json()["capabilities"]
    )
    assert r.client.get("/api/v1/me/canvases", headers=r.headers["owner"]).json()["items"] == []
    assert (
        r.client.get(
            "/api/v1/me/canvases", headers=r.headers["member"], params={"board_id": str(uuid4())}
        ).status_code
        == 404
    )
