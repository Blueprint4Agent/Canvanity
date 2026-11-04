"""Official layout persistence, visitor projection and metadata-only bounded hydration."""

from copy import deepcopy
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.error import AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.asset import Asset, AssetDeletionOutbox, CanvasAssetRef
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardDeleteForm,
    BoardLayout,
    BoardMember,
    BoardMemberAudit,
    BoardRepository,
    Shelf,
    ShelfPolicy,
)
from app.models.board_layout import BoardLayoutSaveForm
from app.models.canvas import Canvas, CanvasDocument, CanvasPublication, CanvasPublicationTag
from app.models.user import User
from app.services.board import BoardService
from app.services.board_layout import BoardLayoutService
from app.services.board_permission import BoardPermissionService
from tests.integration.api.v1.board.test_board_member_administration import roster as roster, window
from tests.integration.api.v1.canvas.test_canvas_feed import AT, seed_feed

pytestmark = pytest.mark.primary_data


def services():
    permissions, repository = BoardPermissionService(), BoardRepository()
    return BoardService(permissions, repository), BoardLayoutService(permissions, repository)


def form(document, revision=0):
    return BoardLayoutSaveForm(expected_revision=revision, reason="공식 홈 운영", document=document)


async def state(test_db, board_id):
    async with test_db() as db:
        row = await db.get(BoardLayout, board_id)
        audits = (
            await db.scalars(
                select(BoardMemberAudit)
                .where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "layout_updated",
                )
                .order_by(BoardMemberAudit.id)
            )
        ).all()
        return (
            deepcopy(row.document),
            row.revision,
            (await db.get(Board, board_id)).revision,
            [(a.id, deepcopy(a.changes)) for a in audits],
        )


async def assert_storage(test_db):
    r = await seed_feed(test_db)
    boards, layout = services()
    board_id = r.boards[0].id
    initial = await layout.get(r.owner.id, board_id)
    # A GET document, including nullable whole-Board source, can be PUT unchanged.
    before = await state(test_db, board_id)
    same = await layout.save(r.owner.id, board_id, form(initial.document.model_dump(mode="json")))
    assert same == initial and await state(test_db, board_id) == before
    desired = initial.document.model_dump(mode="json")
    desired["widgets"].append(
        {
            "id": "cover",
            "type": "board_cover",
            "position": {"x": 0, "y": 0},
            "size": {"width": 100, "height": 100},
        }
    )
    # Preserve existing publication/document/Tag/Asset/ref/outbox while changing only the layout.
    asset_id = uuid4()
    async with test_db() as db:
        db.add(
            Asset(
                id=asset_id,
                board_id=board_id,
                canvas_id=r.canvases[0].id,
                owner_id=r.owner.id,
                object_key="test-layout-existing.webp",
                storage_fingerprint="a" * 64,
                storage_location={"provider": "local"},
                byte_size=1,
                width=1,
                height=1,
                frame_count=1,
                sha256="b" * 64,
                state="ready",
                upload_deadline=AT,
            )
        )
        await db.flush()
        db.add_all(
            [
                CanvasAssetRef(
                    board_id=board_id,
                    canvas_id=r.canvases[0].id,
                    asset_id=asset_id,
                    scope="draft",
                    asset_state="ready",
                ),
                AssetDeletionOutbox(
                    asset_id=asset_id,
                    board_id=board_id,
                    object_key="preserved-job",
                    storage_fingerprint="a" * 64,
                    storage_location={"provider": "local"},
                    reason="unused",
                    available_at=AT,
                ),
            ]
        )
        await db.commit()

    async def preserved():
        async with test_db() as db:
            return [
                [
                    tuple(row)
                    for row in (
                        await db.execute(
                            select(*model.__table__.columns).order_by(
                                *model.__table__.primary_key.columns
                            )
                        )
                    ).all()
                ]
                for model in (
                    Canvas,
                    CanvasDocument,
                    CanvasPublication,
                    CanvasPublicationTag,
                    Asset,
                    CanvasAssetRef,
                    AssetDeletionOutbox,
                )
            ]

    old_data = await preserved()
    saved = await layout.save(r.owner.id, board_id, form(desired))
    assert saved.layout_revision == 1
    assert await preserved() == old_data
    after = await state(test_db, board_id)
    assert after[2] == before[2] and len(after[3]) == 1
    audit = after[3][0][1]
    assert set(audit) == {
        "before_revision",
        "after_revision",
        "before_hash",
        "after_hash",
        "widget_count",
        "reason",
    }
    assert audit["before_revision"] == 0 and audit["after_revision"] == 1
    assert audit["before_hash"] != audit["after_hash"] and audit["widget_count"] == 4
    assert await layout.save(r.owner.id, board_id, form(desired, 1)) == saved
    with pytest.raises(BoardException) as stale:
        await layout.save(r.owner.id, board_id, form(desired))
    assert stale.value.code == BoardErrorCode.LAYOUT_CONFLICT.code
    assert await state(test_db, board_id) == after
    for method in ("flush", "commit"):
        with patch.object(AsyncSession, method, side_effect=SQLAlchemyError("isolated failure")):
            with pytest.raises(BoardException) as failed:
                await layout.save(
                    r.owner.id, board_id, form({"schema_version": 1, "widgets": []}, 1)
                )
            assert failed.value.code == BoardErrorCode.UNAVAILABLE.code
        assert await state(test_db, board_id) == after
    for source in (
        {"board_id": str(r.boards[1].id)},
        {"board_id": str(board_id), "shelf_id": str(r.shelves[1].id)},
        {"board_id": str(board_id), "shelf_id": str(uuid4())},
    ):
        bad = deepcopy(desired)
        bad["widgets"][2]["source"] = source
        with pytest.raises(BoardException) as invalid:
            await layout.save(r.owner.id, board_id, form(bad, 1))
        assert invalid.value.code == BoardErrorCode.INVALID_LAYOUT_SOURCE.code
    # High grades and global admin are not official layout roles. Inactive roles never suffice.
    for role, status, expected in (
        ("member", "active", False),
        ("moderator", "active", False),
        ("admin", "pending", False),
        ("admin", "suspended", False),
        ("admin", "banned", False),
        ("admin", "active", True),
    ):
        async with test_db() as db:
            actor = await db.get(BoardMember, (board_id, r.reader.id))
            actor.role, actor.status, actor.grade_id = role, status, r.grades[0][2].id
            await db.commit()
        for operation in (
            layout.get(r.reader.id, board_id),
            layout.save(r.reader.id, board_id, form(desired, 1)),
        ):
            if expected:
                assert (await operation).layout_revision == 1
            else:
                with pytest.raises(BoardException):
                    await operation
    async with test_db() as db:
        (await db.get(User, r.reader.id)).is_active = False
        await db.commit()
    with pytest.raises(AuthException):
        await layout.get(r.reader.id, board_id)
    with pytest.raises(AuthException):
        await boards.home(r.reader.id, board_id=board_id)
    with pytest.raises(BoardException):
        await layout.get(r.writer.id, r.boards[1].id)
    async with test_db() as db:
        (await db.get(Board, board_id)).status = "archived"
        await db.commit()
    assert (await layout.get(r.owner.id, board_id)).layout_revision == 1
    with pytest.raises(BoardException):
        await layout.save(r.owner.id, board_id, form(desired, 1))
    async with test_db() as db:
        (await db.get(Board, board_id)).status = "active"
        (await db.get(BoardLayout, board_id)).revision = 2**31 - 1
        await db.commit()
    assert (
        await layout.save(r.owner.id, board_id, form(desired, 2**31 - 1))
    ).layout_revision == 2**31 - 1
    with pytest.raises(BoardException) as overflow:
        await layout.save(
            r.owner.id, board_id, form({"schema_version": 1, "widgets": []}, 2**31 - 1)
        )
    assert overflow.value.code == BoardErrorCode.LAYOUT_REVISION_EXHAUSTED.code
    async with test_db() as db:
        (await db.get(BoardLayout, board_id)).revision = 1
        (await db.get(User, r.reader.id)).is_active = True
        (await db.get(BoardMember, (board_id, r.reader.id))).role = "member"
        await db.commit()
    empty = await boards.create(r.owner.id, BoardCreateForm(name="삭제 검증", slug="delete-layout"))
    await layout.save(r.owner.id, empty.id, form({"schema_version": 1, "widgets": []}))
    await boards.delete_board(
        r.owner.id, empty.id, BoardDeleteForm(expected_revision=0, confirm_slug=empty.slug)
    )
    async with test_db() as db:
        assert await db.get(BoardLayout, empty.id) is None
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMemberAudit)
                .where(BoardMemberAudit.board_id == empty.id)
            )
            == 0
        )
        assert await db.get(Asset, asset_id) is not None
    return r


async def assert_projection(test_db, r):
    boards, layout = services()
    board_id = r.boards[0].id
    async with test_db() as db:
        hidden, private = [
            Shelf(
                id=uuid4(),
                board_id=board_id,
                name=name,
                slug=slug,
                description="secret-description",
                sort_order=index,
                purpose="general",
                is_visible=visible,
                is_default=False,
            )
            for name, slug, index, visible in (
                ("숨긴 메뉴", "hidden", 2, False),
                ("비밀 회원 Shelf", "private", 3, True),
            )
        ]
        db.add_all([hidden, private])
        await db.flush()
        db.add(
            ShelfPolicy(
                board_id=board_id,
                shelf_id=private.id,
                action="read_canvas",
                audience="members",
                min_grade_id=r.grades[0][2].id,
                staff_only=False,
                staff_bypass=False,
            )
        )
        for shelf, title in ((hidden, "숨긴 메뉴 공개본"), (private, "기밀 공개본")):
            canvas = Canvas(
                id=uuid4(),
                board_id=board_id,
                shelf_id=shelf.id,
                author_id=r.writer.id,
                title="기밀 초안",
                summary="초안 요약",
                visibility="public",
            )
            db.add(canvas)
            await db.flush()
            db.add(
                CanvasPublication(
                    canvas_id=canvas.id,
                    publication_revision=1,
                    source_metadata_revision=0,
                    source_document_revision=0,
                    title=title,
                    summary="게시 요약",
                    visibility="public",
                    document={"never-select": "secret"},
                    published_at=AT,
                )
            )
        await db.commit()
    current = await layout.get(r.owner.id, board_id)
    document = current.document.model_dump(mode="json")
    latest = document["widgets"][2]
    for ident, shelf in (
        ("private-custom-secret-id", private.id),
        ("hidden-source", hidden.id),
        ("same-source-again", None),
    ):
        widget = deepcopy(latest)
        widget["id"] = ident
        widget["source"]["shelf_id"] = str(shelf) if shelf else None
        widget["source"]["limit"] = 1
        document["widgets"].append(widget)
    await layout.save(r.owner.id, board_id, form(document, current.layout_revision))
    statements = []
    async with test_db() as db:
        engine = db.bind

    def observe(connection, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", observe)
    try:
        home = await boards.home(None, board_id=board_id)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", observe)
    text = home.model_dump_json()
    assert str(private.id) not in text and "private-custom-secret-id" not in text
    assert "비밀 회원 Shelf" not in text and "기밀 공개본" not in text and "기밀 초안" not in text
    assert "hidden-source" in text and "숨긴 메뉴 공개본" in text
    assert hidden.id not in [s.id for s in home.shelves]
    assert str(private.id) in (await layout.get(r.owner.id, board_id)).model_dump_json()
    assert next(d for d in home.widget_data if d.type == "board_cover").media is None
    collection = [d for d in home.widget_data if d.type == "canvas_collection"]
    assert all(item.view == "publication" for d in collection for item in d.items)
    old = next(item for d in collection for item in d.items if item.canvas.id.int == 900)
    assert old.canvas.title == "공개 제목 900" and old.canvas.tags[0].id == r.old.id
    assert all(item.canvas.id.int != 994 for d in collection for item in d.items)
    owner_home = await boards.home(r.owner.id, board_id=board_id)
    assert "private-custom-secret-id" not in owner_home.model_dump_json()
    assert all(
        item.canvas.id.int != 994
        for d in owner_home.widget_data
        if d.type == "canvas_collection"
        for item in d.items
    )
    batch = [s for s in statements if "home_sources AS" in s]
    assert len(batch) == 1 and "row_number()" in batch[0].lower()
    assert "canvas_publications.document" not in batch[0] and "canvas_documents" not in batch[0]
    assert "canvas_tags" not in batch[0] and "canvas_publication_tags" in batch[0]
    assert (
        batch[0].split("readable_boards AS")[0].count(" AS source_index") == 3
    )  # Board + hidden + private, duplicate Board reused.
    # Readable private source becomes visible on promotion; it disappears again on revocation.
    promoted = await boards.home(r.reader.id, board_id=board_id)
    assert "기밀 공개본" in promoted.model_dump_json()
    async with test_db() as db:
        (await db.get(BoardMember, (board_id, r.reader.id))).grade_id = r.grades[0][0].id
        await db.delete(await db.get(ShelfPolicy, (board_id, private.id, "read_canvas")))
        # Remove the secret content before deleting its now-empty source Shelf.
        secret = await db.scalar(select(Canvas).where(Canvas.shelf_id == private.id))
        await db.delete(secret)
        await db.flush()
        await db.delete(await db.get(Shelf, private.id))
        await db.commit()
    assert (
        "private-custom-secret-id"
        not in (await boards.home(None, board_id=board_id)).model_dump_json()
    )
    assert "private-custom-secret-id" in (await layout.get(r.owner.id, board_id)).model_dump_json()
    return document


async def assert_collection_bounds(test_db, r):
    boards, layouts = services()
    target = await boards.create(r.owner.id, BoardCreateForm(name="위젯 상한", slug="bounded-home"))
    current = await layouts.get(r.owner.id, target.id)
    async with test_db() as db:
        shelf = await db.scalar(
            select(Shelf).where(Shelf.board_id == target.id, Shelf.is_default.is_(True))
        )
        for ident in range(1, 26):
            canvas = Canvas(
                id=UUID(int=10000 + ident),
                board_id=target.id,
                shelf_id=shelf.id,
                author_id=r.owner.id,
                title="공개하면 안 되는 초안",
                visibility="public",
            )
            db.add(canvas)
            await db.flush()
            db.add(
                CanvasPublication(
                    canvas_id=canvas.id,
                    publication_revision=1,
                    source_metadata_revision=0,
                    source_document_revision=0,
                    title=f"공개 순서 {ident}",
                    summary="고정 요약",
                    visibility="public",
                    document={},
                    published_at=AT,
                )
            )
        await db.commit()
    template = current.document.model_dump(mode="json")["widgets"][2]
    template["source"]["limit"] = 20
    document = {
        "schema_version": 1,
        "widgets": [dict(deepcopy(template), id=f"source-{n}") for n in range(100)],
    }
    await layouts.save(r.owner.id, target.id, form(document))
    result = await boards.home(None, board_id=target.id)
    assert len(result.widget_data) == 100
    assert all(len(data.items) == 20 for data in result.widget_data)
    assert [item.canvas.id.int for item in result.widget_data[0].items] == list(
        range(10025, 10005, -1)
    )
    assert "공개하면 안 되는 초안" not in result.model_dump_json()


def test_sqlite_layout_storage_roles_failure_preservation_and_visitor_projection(
    integration_client,
):
    async def run():
        r = await assert_storage(get_db)
        await assert_projection(get_db, r)
        await assert_collection_bounds(get_db, r)

    integration_client.portal.call(run)


def test_management_http_auth_audit_and_home_alias(roster):
    r = roster
    path = r.path + "/layout"
    assert r.client.get(path).status_code == 401
    for name in ("moderator", "member", "outsider"):
        assert r.client.get(path, headers=r.headers[name]).status_code == 403
    got = r.client.get(path, headers=r.headers["admin"])
    assert got.status_code == 200
    document = got.json()["document"]
    document["widgets"] = []
    saved = r.client.put(
        path,
        headers=r.headers["admin"],
        json={
            "expected_revision": 0,
            "reason": "공식 홈 정리",
            "document": document,
        },
    )
    assert saved.status_code == 200 and saved.json()["layout_revision"] == 1
    audit = r.client.get(r.path + "/member-audit", headers=r.headers["owner"], params=window())
    entry = next(row for row in audit.json()["items"] if row["action"] == "layout_updated")
    assert entry["layout_change"]["after_revision"] == 1 and entry["before"] is None
    by_id = r.client.get(r.path + "/home").json()
    by_slug = r.client.get("/api/v1/boards/by-slug/" + r.board["slug"]).json()
    assert by_id == by_slug and by_id["widget_data"] == []
    api_key = r.client.post("/api/v1/api-keys", headers=r.headers["owner"], json={"name": "layout"})
    key_headers = {"X-API-Key": api_key.json()["api_key"]}
    assert r.client.get(path, headers=key_headers).status_code == 401
    assert (
        r.client.put(
            path,
            headers=key_headers,
            json={
                "expected_revision": 1,
                "reason": "키 인증 거부",
                "document": document,
            },
        ).status_code
        == 401
    )
