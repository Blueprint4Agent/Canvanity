"""HTTP/SQLite free-tag reuse and atomic metadata/document isolation."""

import asyncio
import sqlite3
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.db.session import get_db
from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.tag_exception import TagErrorCode, TagException
from app.models.canvas import Canvas, CanvasDocument
from app.models.tag import CanvasTag, Tag, TagCreateForm, TagRepository, TagSearchQuery
from app.models.user import User
from tests.fixtures.canvas_document_data import canvas_document
from tests.integration.api.v1.asset.test_canvas_assets import images as images, upload
from tests.integration.api.v1.board.test_board_creation import PAYLOAD, signup
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_document_save import persisted, save
from tests.integration.api.v1.canvas.test_canvas_drafts import (
    board_write,
    create,
    draft as draft,
    extra_shelf,
    mutate,
    promote,
    snapshot,
)

pytestmark = pytest.mark.primary_data


def tag(r, name, *, actor="member"):
    result = r.client.post("/api/v1/tags", headers=r.headers[actor], json={"name": name})
    assert result.status_code in {200, 201}, result.text
    return result.json()


def links(r):
    async def read():
        async with get_db() as db:
            return list(
                (
                    await db.execute(
                        select(CanvasTag.canvas_id, CanvasTag.tag_id).order_by(
                            CanvasTag.canvas_id, CanvasTag.tag_id
                        )
                    )
                ).all()
            )

    return r.client.portal.call(read)


def test_public_dictionary_normalized_reuse_literal_search_and_no_content_leak(draft):
    r = draft
    names = ["  C++ ", "C#", "한글", "Straße", "가", "100%", "under_score", "slash/back\\"]
    created = [tag(r, name) for name in names]
    for name, index in [("c++", 0), ("STRASSE", 3), ("가", 4)]:
        reused = r.client.post("/api/v1/tags", headers=r.headers["peer"], json={"name": name})
        assert reused.status_code == 200 and reused.json() == created[index]
    assert mutate(r, tag_ids=[created[0]["id"]]).status_code == 200
    for query, index in [
        ("c++", 0),
        ("#", 1),
        ("한", 2),
        ("strasse", 3),
        ("%", 5),
        ("_", 6),
        ("/back\\", 7),
    ]:
        result = r.client.get("/api/v1/tags", params={"q": query})
        assert result.status_code == 200 and result.json() == {"items": [created[index]]}
        assert set(result.json()["items"][0]) == {"id", "name"}
    first_two = r.client.get("/api/v1/tags", params={"limit": 2}).json()["items"]
    assert first_two == sorted(created, key=lambda item: item["name"].casefold())[:2]
    assert r.client.get("/api/v1/tags", params={"q": "' OR 1=1 --"}).json() == {"items": []}


def test_sqlite_concurrent_get_or_create_preserves_first_display_name(integration_client):
    _, user_id = signup(integration_client, "tag-race")

    async def race():
        repository = TagRepository()
        results = await asyncio.gather(
            *[
                repository.get_or_create(user_id, TagCreateForm(name=name))
                for name in ["Straße", "STRASSE", " strasse ", "straße"]
            ]
        )
        assert sum(result.created for result in results) == 1
        assert len({result.tag.id for result in results}) == 1
        assert len({result.tag.name for result in results}) == 1
        catalog = await repository.search(TagSearchQuery())
        assert catalog.items == [results[0].tag]

    integration_client.portal.call(race)


def test_tags_are_shared_by_canvases_across_boards_and_are_not_board_interest_inputs(draft):
    r = draft
    common, second = tag(r, "한글"), tag(r, "C++")
    patched = mutate(r, tag_ids=[common["id"]])
    assert patched.status_code == 200
    own = create(r, tag_ids=[common["id"], second["id"]])
    assert own.status_code == 201
    other = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={**PAYLOAD, "slug": "tag-foreign", "name": "다른 보드"},
    )
    assert other.status_code == 201
    path = f"/api/v1/boards/{other.json()['id']}"
    shelf = next(
        s["id"]
        for s in r.client.get(path + "/shelves", headers=r.headers["owner"]).json()["items"]
        if s["is_default"]
    )
    cross = r.client.post(
        path + "/canvases",
        headers=r.headers["owner"],
        json={"shelf_id": shelf, "title": "같은 태그", "tag_ids": [common["id"]]},
    )
    assert cross.status_code == 201 and cross.json()["canvas"]["tags"] == [common]
    assert len(links(r)) == 4
    ten = [tag(r, f"태그 {index}")["id"] for index in range(10)]
    maximum = create(r, tag_ids=ten)
    assert maximum.status_code == 201 and len(maximum.json()["canvas"]["tags"]) == 10
    rejected = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={**PAYLOAD, "slug": "tag-not-interest", "tag_ids": [common["id"]]},
    )
    assert rejected.status_code == 422
    catalog = r.client.get("/api/v1/interests").json()["items"]
    assert len(catalog) == 40 and all("name_ko" in item and "name_en" in item for item in catalog)


def test_metadata_tags_are_atomic_single_revision_noop_and_preserve_document_asset_refs(images):
    r = images
    first, second = tag(r, "한글"), tag(r, "C++")
    asset = upload(r).json()["id"]
    assert save(r, canvas_document(asset)).status_code == 200
    before_document = persisted(r)
    shelf = extra_shelf(r)
    result = mutate(
        r,
        title="제목과 태그",
        summary="설명",
        shelf_id=shelf["id"],
        visibility="public",
        tag_ids=[first["id"], second["id"]],
    )
    assert result.status_code == 200, result.text
    assert result.json()["canvas"]["revision"] == 1
    assert result.json()["document_revision"] == 1
    assert result.json()["canvas"]["tags"] == [second, first]
    assert persisted(r) == before_document
    no_op = mutate(r, tag_ids=[second["id"], first["id"]])
    assert no_op.status_code == 200 and no_op.json() == result.json()
    stale = r.client.patch(
        r.canvas_path,
        headers=r.headers["member"],
        json={"expected_revision": 0, "tag_ids": [first["id"], second["id"]]},
    )
    assert stale.status_code == 409 and stale.json()["detail"]["details"] == {"current_revision": 1}
    unchanged = mutate(r, summary="태그 생략 시 유지")
    assert unchanged.status_code == 200 and unchanged.json()["canvas"]["tags"] == [second, first]
    removed = mutate(r, tag_ids=[])
    assert removed.status_code == 200 and removed.json()["canvas"]["tags"] == []
    assert removed.json()["canvas"]["revision"] == 3
    assert links(r) == [] and persisted(r) == before_document


def test_missing_tag_or_storage_failure_rolls_back_all_metadata_and_creation(draft):
    r = draft
    first, second = tag(r, "C++"), tag(r, "C#")
    assert mutate(r, tag_ids=[first["id"]]).status_code == 200
    before, before_links = snapshot(r), links(r)
    for operation in ("patch", "create"):
        result = (
            mutate(r, title="원자적 거부", tag_ids=[second["id"], str(uuid4())])
            if operation == "patch"
            else create(r, tag_ids=[str(uuid4())])
        )
        assert (
            result.status_code == 422 and result.json()["detail"]["error"] == "CANVAS_INVALID_TAGS"
        )
        assert snapshot(r) == before and links(r) == before_links
    original_flush = AsyncSession.flush

    async def broken_flush(db, *args, **kwargs):
        await original_flush(db, *args, **kwargs)
        raise SQLAlchemyError("after link replacement")

    for target, options in [
        ("flush", {"new": broken_flush}),
        ("commit", {"side_effect": SQLAlchemyError("commit failed")}),
    ]:
        with patch.object(AsyncSession, target, **options):
            result = mutate(r, title="모두 rollback", tag_ids=[second["id"]])
        assert result.status_code == 503
        assert snapshot(r) == before and links(r) == before_links


def test_tag_mutations_apply_current_author_membership_shelf_board_and_draft_guards(draft):
    r = draft
    item = tag(r, "C#")
    for actor in ("owner", "admin", "moderator", "peer", "outsider"):
        assert mutate(r, actor=actor, tag_ids=[item["id"]]).status_code == 404
    before = snapshot(r)
    promote(r, grade=0)
    assert mutate(r, tag_ids=[item["id"]]).status_code == 403
    assert snapshot(r)[1:] == before[1:]
    promote(r, grade=1)
    assert mutate(r, method="DELETE").status_code == 204
    assert mutate(r, tag_ids=[item["id"]]).status_code == 409
    assert mutate(r, method="POST", suffix="/restore").status_code == 200
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert mutate(r, tag_ids=[item["id"]]).status_code == 403
    assert links(r) == []


def test_tag_repository_rechecks_active_account_and_translates_unknown_database_errors(
    integration_client,
):
    _, user_id = signup(integration_client, "tag-active")

    async def check():
        repository = TagRepository()
        async with get_db() as db:
            (await db.get(User, user_id)).is_active = False
            await db.commit()
        with pytest.raises(AuthException) as inactive:
            await repository.get_or_create(user_id, TagCreateForm(name="거부"))
        assert inactive.value.code == AuthErrorCode.USER_NOT_FOUND.code
        with patch.object(AsyncSession, "scalars", side_effect=SQLAlchemyError("search failed")):
            with pytest.raises(TagException) as unavailable:
                await repository.search(TagSearchQuery())
        assert unavailable.value.code == TagErrorCode.UNAVAILABLE.code
        async with get_db() as db:
            (await db.get(User, user_id)).is_active = True
            await db.commit()
        with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("create failed")):
            with pytest.raises(TagException):
                await repository.get_or_create(user_id, TagCreateForm(name="rollback"))
        assert (await repository.search(TagSearchQuery())).items == []

    integration_client.portal.call(check)


def test_populated_sqlite_tag_migration_preserves_all_content_and_checks_foreign_keys(
    images, tmp_path, monkeypatch
):
    r = images
    asset = upload(r).json()["id"]
    assert save(r, canvas_document(asset)).status_code == 200
    clone = tmp_path / "tag-migration.db"
    with (
        sqlite3.connect(make_url(SETTINGS.DATABASE_URL).database) as source,
        sqlite3.connect(clone) as target,
    ):
        source.backup(target)
    url = f"sqlite+aiosqlite:///{clone}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    config = _build_alembic_config(url)
    command.downgrade(config, "0027_canvas_assets")
    tables = (
        "canvases",
        "canvas_documents",
        "assets",
        "canvas_asset_refs",
        "asset_deletion_outbox",
        "users",
        "boards",
    )

    def state():
        with sqlite3.connect(clone) as db:
            return {
                table: db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
                for table in tables
            }

    before = state()
    command.upgrade(config, "head")
    assert state() == before
    with sqlite3.connect(clone) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0034_canvas_views",
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    command.downgrade(config, "0027_canvas_assets")
    command.upgrade(config, "head")
    assert state() == before


def test_canvas_delete_cascades_links_account_delete_keeps_tags_and_foreign_keys_restrict(draft):
    r = draft
    item = tag(r, "한글")
    assert mutate(r, tag_ids=[item["id"]]).status_code == 200

    async def check():
        canvas_id, tag_id = UUID(r.canvas["canvas"]["id"]), UUID(item["id"])
        async with get_db() as db:
            db.add(CanvasTag(canvas_id=canvas_id, tag_id=uuid4()))
            with pytest.raises(IntegrityError):
                await db.commit()
        async with get_db() as db:
            with pytest.raises(IntegrityError):
                await db.execute(delete(Tag).where(Tag.id == tag_id))
                await db.commit()
        async with get_db() as db:
            await db.execute(delete(User).where(User.id == r.ids["member"]))
            await db.commit()
        async with get_db() as db:
            assert (await db.get(Canvas, canvas_id)).author_id is None
            assert await db.get(CanvasTag, (canvas_id, tag_id)) is not None
            await db.execute(delete(Canvas).where(Canvas.id == canvas_id))
            await db.commit()
        async with get_db() as db:
            assert await db.get(CanvasDocument, canvas_id) is None
            assert await db.get(CanvasTag, (canvas_id, tag_id)) is None
            assert (await db.get(Tag, tag_id)).name == "한글"

    r.client.portal.call(check)
