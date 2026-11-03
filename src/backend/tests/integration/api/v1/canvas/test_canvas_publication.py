"""HTTP/SQLite publication snapshots, current access, state CAS and file references."""

import asyncio
import sqlite3
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.db.session import get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.asset import Asset, AssetDeletionOutbox, AssetTransaction, CanvasAssetRef
from app.models.board import ACTIONS, Board, BoardMember
from app.models.canvas import (
    MAX_CANVAS_REVISION,
    Canvas,
    CanvasDocument,
    CanvasPublication,
    CanvasPublicationCounter,
    CanvasPublicationTag,
    CanvasPublishForm,
    CanvasRepository,
    CanvasUnpublishForm,
)
from app.models.tag import CanvasTag, Tag
from app.models.user import User
from app.services.canvas import CanvasService
from tests.fixtures.canvas_document_data import canvas_document
from tests.integration.api.v1.asset.test_canvas_assets import (
    drain,
    due_now,
    images as images,
    upload,
)
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import (
    revision,
    roster as roster,
)
from tests.integration.api.v1.canvas.test_canvas_document_save import save
from tests.integration.api.v1.canvas.test_canvas_drafts import (
    board_write,
    draft as draft,
    extra_shelf,
    mutate,
    promote,
)
from tests.integration.api.v1.tag.test_canvas_tags import tag

pytestmark = pytest.mark.primary_data
PUBLICATION_MODELS = (
    Canvas,
    CanvasDocument,
    CanvasPublicationCounter,
    CanvasPublication,
    CanvasPublicationTag,
    CanvasTag,
    Asset,
    CanvasAssetRef,
    AssetDeletionOutbox,
)


def publication_form(r):
    current = r.client.get(r.canvas_path, headers=r.headers["member"])
    assert current.status_code == 200, current.text
    data = current.json()
    return {
        "expected_metadata_revision": data["canvas"]["revision"],
        "expected_document_revision": data["document_revision"],
        "expected_publication_revision": data["publication_revision"],
    }


def publish(r, *, actor="member", **fields):
    return r.client.post(
        r.canvas_path + "/publish",
        headers=r.headers[actor],
        json={**publication_form(r), **fields},
    )


def unpublish(r, *, actor="member", revision=None):
    if revision is None:
        revision = publication_form(r)["expected_publication_revision"]
    return r.client.post(
        r.canvas_path + "/unpublish",
        headers=r.headers[actor],
        json={"expected_publication_revision": revision},
    )


async def database_state(test_db=get_db, models=PUBLICATION_MODELS):
    async with test_db() as db:
        return [
            [
                tuple(getattr(row, column.name) for column in model.__table__.columns)
                for row in (
                    await db.scalars(select(model).order_by(*model.__table__.primary_key.columns))
                ).all()
            ]
            for model in models
        ]


def state(r):
    return r.client.portal.call(database_state)


def test_published_metadata_document_tags_and_images_are_frozen_until_republish(images):
    r = images
    first, second, unused = [upload(r).json() for _ in range(3)]
    old, new = tag(r, "먼저 공개한 태그"), tag(r, "수정 초안 태그")
    assert mutate(r, title="공개 제목", summary="공개 요약", tag_ids=[old["id"]]).status_code == 200
    assert save(r, canvas_document(first["id"])).status_code == 200
    before_form = publication_form(r)
    posted = publish(r)
    assert posted.status_code == 200, posted.text
    assert posted.headers["cache-control"] == "private, no-store"
    assert posted.json()["metadata_revision"] == before_form["expected_metadata_revision"]
    assert posted.json()["document_revision"] == before_form["expected_document_revision"]
    assert posted.json()["publication_revision"] == 1
    public = r.client.get(r.canvas_path).json()
    body = r.client.get(r.canvas_path + "/document").json()
    assert public["view"] == "publication" and public["canvas"]["status"] == "published"
    assert public["canvas"]["tags"] == [old]
    assert set(public["canvas"]) == {
        "id",
        "board_id",
        "shelf_id",
        "author_id",
        "title",
        "summary",
        "visibility",
        "status",
        "tags",
    }
    assert set(public) == {
        "canvas",
        "view",
        "capabilities",
        "publication_revision",
        "source_metadata_revision",
        "source_document_revision",
        "published_at",
    }
    assert body["revision"] == body["source_document_revision"] == 1
    assert public["source_metadata_revision"] == 1
    assert all(
        not allowed for name, allowed in public["capabilities"].items() if name != "read_document"
    )
    frozen = state(r)
    assert publish(r).json() == posted.json() and state(r) == frozen
    stale = publish(r, expected_publication_revision=0)
    assert stale.status_code == 409
    assert stale.json()["detail"]["error"] == "CANVAS_PUBLICATION_REVISION_CONFLICT"
    assert state(r) == frozen
    assert (
        mutate(
            r, title="공개하면 안 되는 초안", summary="초안 요약", tag_ids=[new["id"]]
        ).status_code
        == 200
    )
    assert save(r, canvas_document(second["id"]), revision=1).status_code == 200
    assert r.client.get(r.canvas_path).json() == public
    assert r.client.get(r.canvas_path + "/document").json() == body
    own = r.client.get(r.canvas_path, headers=r.headers["member"]).json()
    assert own["view"] == "draft" and own["canvas"]["status"] == "draft"
    assert own["publication"]["publication_revision"] == 1
    assert own["capabilities"]["publish"] and own["capabilities"]["unpublish"]
    assert own["canvas"]["tags"] == [new]
    for actor in (None, "owner", "admin", "moderator", "peer", "outsider"):
        headers = r.headers[actor] if actor else {}
        assert r.client.get(r.canvas_path, headers=headers).json() == public
        assert (
            r.client.get(r.canvas_path, headers=headers, params={"view": "draft"}).status_code
            == 404
        )
        assert r.client.get(first["url"], headers=headers).status_code == 200
        for image in (second, unused):
            assert r.client.get(image["url"], headers=headers).status_code == 404
    for image in (first, second, unused):
        assert r.client.get(image["url"], headers=r.headers["member"]).status_code == 200
    assert (
        r.client.get(
            second["url"], headers=r.headers["member"], params={"view": "publication"}
        ).status_code
        == 404
    )
    assert publish(r, expected_metadata_revision=1).status_code == 409
    assert publish(r, expected_document_revision=1).status_code == 409
    refreshed = publish(r)
    assert refreshed.status_code == 200 and refreshed.json()["publication_revision"] == 2
    assert r.client.get(r.canvas_path).json()["canvas"]["title"] == "공개하면 안 되는 초안"
    assert r.client.get(r.canvas_path).json()["canvas"]["tags"] == [new]
    assert r.client.get(first["url"]).status_code == 404
    assert r.client.get(second["url"]).status_code == 200
    assert r.client.get(r.canvas_path + "/document").json()["document"] == canvas_document(
        second["id"]
    )


def test_visibility_intersection_and_current_shelf_move_take_effect_immediately(images):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert publish(r).status_code == 200
    original = r.client.get(r.canvas_path).json()
    assert mutate(r, visibility="members").status_code == 200
    for path in (r.canvas_path, r.canvas_path + "/document", image["url"]):
        assert r.client.get(path).status_code == 404
        assert r.client.get(path, headers=r.headers["peer"]).status_code == 200
    assert publish(r).status_code == 200
    assert mutate(r, visibility="public").status_code == 200
    assert r.client.get(r.canvas_path).status_code == 404  # broadening needs a new snapshot
    assert publish(r).status_code == 200
    assert r.client.get(r.canvas_path).status_code == 200
    target = extra_shelf(r)
    actions = {action: None for action in ACTIONS}
    actions["read_canvas"] = {
        "audience": "members",
        "min_grade_id": r.grades[1]["id"],
        "staff_only": False,
        "staff_bypass": True,
    }
    assert (
        board_write(
            r, "PUT", f"/api/v1/shelves/{target['id']}/policies", actions=actions
        ).status_code
        == 200
    )
    assert mutate(r, shelf_id=target["id"]).status_code == 200
    assert r.client.get(r.canvas_path).status_code == 404
    assert r.client.get(image["url"], headers=r.headers["peer"]).status_code == 404
    visible = r.client.get(r.canvas_path, headers=r.headers["owner"]).json()
    assert visible["canvas"]["shelf_id"] == target["id"]
    assert visible["canvas"]["title"] == original["canvas"]["title"]
    assert visible["source_metadata_revision"] == 2
    assert r.client.get(image["url"], headers=r.headers["owner"]).status_code == 200


@pytest.mark.parametrize(
    "restriction",
    ["members", "private", "pending", "suspended", "banned", "left", "grade", "board_suspended"],
)
def test_publication_metadata_document_and_image_share_current_access_boundary(images, restriction):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert publish(r).status_code == 200
    headers = r.headers["peer"]
    if restriction == "members":
        assert mutate(r, visibility="members").status_code == 200
        headers = r.headers["outsider"]
    elif restriction == "private":
        assert (
            board_write(r, "PATCH", r.path, visibility="private", join_policy="invite").status_code
            == 200
        )
        headers = r.headers["outsider"]
    elif restriction == "grade":
        actions = {action: None for action in ACTIONS}
        actions["read_canvas"] = {
            "audience": "members",
            "min_grade_id": r.grades[1]["id"],
            "staff_only": False,
            "staff_bypass": False,
        }
        assert (
            board_write(
                r, "PUT", f"/api/v1/shelves/{r.shelf_id}/policies", actions=actions
            ).status_code
            == 200
        )
    else:

        async def restrict():
            async with get_db() as db:
                if restriction == "board_suspended":
                    (await db.get(Board, UUID(r.board["id"]))).status = "suspended"
                elif restriction == "left":
                    await db.delete(await db.get(BoardMember, (UUID(r.board["id"]), r.ids["peer"])))
                else:
                    (
                        await db.get(BoardMember, (UUID(r.board["id"]), r.ids["peer"]))
                    ).status = restriction
                await db.commit()

        if restriction in {"pending", "left"}:
            assert mutate(r, visibility="members").status_code == 200
        r.client.portal.call(restrict)
    before = state(r)
    for path in (r.canvas_path, r.canvas_path + "/document", image["url"]):
        denied = r.client.get(path, headers=headers)
        assert denied.status_code == 404, denied.text
        assert denied.json()["detail"]["error"] == "CANVAS_NOT_FOUND"
    assert state(r) == before


def test_unpublish_state_cas_prevents_aba_and_low_grade_author_can_withdraw(images):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    old_form = publication_form(r)
    assert publish(r).json()["publication_revision"] == 1
    published_form = publication_form(r)
    promote(r, grade=0)
    own = r.client.get(r.canvas_path, headers=r.headers["member"]).json()
    assert own["capabilities"]["unpublish"] and not own["capabilities"]["publish"]
    assert unpublish(r).json()["publication_revision"] == 2
    assert unpublish(r).json()["publication_revision"] == 2
    assert r.client.get(image["url"]).status_code == 404
    assert r.client.get(image["url"], headers=r.headers["member"]).status_code == 200
    promote(r)
    before = state(r)
    for form in (old_form, published_form):
        stale = r.client.post(r.canvas_path + "/publish", headers=r.headers["member"], json=form)
        assert stale.status_code == 409
        assert stale.json()["detail"]["error"] == "CANVAS_PUBLICATION_REVISION_CONFLICT"
    assert state(r) == before
    assert publish(r).json()["publication_revision"] == 3
    assert unpublish(r, revision=1).status_code == 409
    assert r.client.get(r.canvas_path).status_code == 200
    for actor in ("owner", "admin", "moderator", "peer", "outsider"):
        assert publish(r, actor=actor).status_code == 404
        assert unpublish(r, actor=actor).status_code == 404
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert r.client.get(r.canvas_path).status_code == 200
    assert not r.client.get(r.canvas_path, headers=r.headers["member"]).json()["capabilities"][
        "unpublish"
    ]
    assert unpublish(r).status_code == 403 and publish(r).status_code == 403


def test_trash_restore_and_author_set_null_never_republish_or_leak_account_data(images):
    r = images
    image = upload(r).json()
    item = tag(r, "보존할 공개 태그")
    assert mutate(r, tag_ids=[item["id"]]).status_code == 200
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert publish(r).status_code == 200
    assert mutate(r, "DELETE").status_code == 204
    assert r.client.get(r.canvas_path).status_code == 404
    own = r.client.get(r.canvas_path, headers=r.headers["member"]).json()
    assert own["publication"] is None and own["publication_revision"] == 2
    assert mutate(r, "POST", suffix="/restore").status_code == 200
    assert r.client.get(r.canvas_path).status_code == 404
    assert publish(r).json()["publication_revision"] == 3
    before = r.client.get(r.canvas_path).json()

    async def remove_author():
        async with get_db() as db:
            await db.execute(delete(User).where(User.id == r.ids["member"]))
            await db.commit()

    r.client.portal.call(remove_author)
    after = r.client.get(r.canvas_path).json()
    assert after["canvas"].pop("author_id") is None
    before["canvas"].pop("author_id")
    assert after == before
    assert r.client.get(image["url"]).status_code == 200
    assert r.client.get(r.canvas_path, headers=r.headers["member"]).status_code == 404
    assert r.client.get(r.canvas_path, params={"view": "draft"}).status_code == 404


@pytest.mark.parametrize("operation", ["publish", "unpublish", "trash"])
@pytest.mark.parametrize("failure", ["flush", "commit"])
def test_publication_refs_counter_tags_and_content_roll_back_together(images, operation, failure):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert mutate(r, tag_ids=[tag(r, "원자성 태그")["id"]]).status_code == 200
    if operation != "publish":
        assert publish(r).status_code == 200
    before = state(r)
    original = AssetTransaction.replace_refs

    async def invalid_ref(tx, canvas, ids, *, scope):
        await original(tx, canvas, ids, scope=scope)
        tx._db.add(
            CanvasAssetRef(
                canvas_id=canvas.id, board_id=canvas.board_id, asset_id=uuid4(), scope=scope
            )
        )
        await tx._db.flush()

    target = AssetTransaction if failure == "flush" else AsyncSession
    method = "replace_refs" if failure == "flush" else "commit"
    options = (
        {"new": invalid_ref}
        if failure == "flush"
        else {"side_effect": SQLAlchemyError("controlled commit failure")}
    )
    with patch.object(target, method, **options):
        response = (
            publish(r)
            if operation == "publish"
            else unpublish(r)
            if operation == "unpublish"
            else mutate(r, "DELETE")
        )
    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "CANVAS_UNAVAILABLE"
    assert state(r) == before


def test_ambiguous_committed_publish_is_reconciled_without_deleting_files(images):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    original = AsyncSession.commit

    async def lost_response(db):
        await original(db)
        raise SQLAlchemyError("commit response lost")

    with patch.object(AsyncSession, "commit", new=lost_response):
        assert publish(r).status_code == 503
    assert r.client.get(r.canvas_path).json()["publication_revision"] == 1
    assert r.client.get(image["url"]).status_code == 200
    assert publish(r).json()["publication_revision"] == 1


def test_publication_overflow_noop_and_invalid_stored_document_leave_state_intact(images):
    r = images
    assert publish(r).status_code == 200

    async def overflow():
        async with get_db() as db:
            (await db.get(CanvasPublicationCounter, r.canvas_id)).revision = MAX_CANVAS_REVISION
            (
                await db.get(CanvasPublication, r.canvas_id)
            ).publication_revision = MAX_CANVAS_REVISION
            await db.commit()

    r.client.portal.call(overflow)
    assert publish(r).json()["publication_revision"] == MAX_CANVAS_REVISION
    before = state(r)
    assert unpublish(r).status_code == 409
    assert mutate(r, "DELETE").status_code == 409
    assert state(r) == before
    assert mutate(r, title="게시 clock 상한과 별도 초안").status_code == 200
    before = state(r)
    assert publish(r).status_code == 409 and state(r) == before

    async def invalid():
        async with get_db() as db:
            (await db.get(CanvasPublicationCounter, r.canvas_id)).revision = 1
            (await db.get(CanvasPublication, r.canvas_id)).publication_revision = 1
            (await db.get(CanvasDocument, r.canvas_id)).document = {"schema_version": 999}
            await db.commit()

    r.client.portal.call(invalid)
    before = state(r)
    rejected = publish(r)
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["error"] == "CANVAS_DOCUMENT_INVALID"
    assert state(r) == before


def test_two_sqlite_connections_and_stale_bidirectional_state_changes_have_one_winner(images):
    r = images
    service = CanvasService(r.access, CanvasRepository())

    async def race():
        form = CanvasPublishForm(
            expected_metadata_revision=0,
            expected_document_revision=0,
            expected_publication_revision=0,
        )
        return await asyncio.gather(
            *[service.publish(r.ids["member"], r.canvas_id, form) for _ in range(2)],
            return_exceptions=True,
        )

    results = r.client.portal.call(race)
    assert sum(not isinstance(item, Exception) for item in results) == 1
    loser = next(item for item in results if isinstance(item, Exception))
    assert (
        isinstance(loser, CanvasException)
        and loser.code == CanvasErrorCode.PUBLICATION_CONFLICT.code
    )

    async def oppose():
        return await asyncio.gather(
            service.publish(
                r.ids["member"],
                r.canvas_id,
                CanvasPublishForm(
                    expected_metadata_revision=0,
                    expected_document_revision=0,
                    expected_publication_revision=1,
                ),
            ),
            service.unpublish(
                r.ids["member"], r.canvas_id, CanvasUnpublishForm(expected_publication_revision=1)
            ),
            return_exceptions=True,
        )

    results = r.client.portal.call(oppose)
    assert any(not isinstance(item, Exception) for item in results)
    assert r.client.get(r.canvas_path).status_code == 404
    assert publish(r, expected_publication_revision=1).status_code == 409
    assert publish(r).json()["publication_revision"] == 3


def test_publication_refs_protect_cleanup_then_unpublish_preserves_draft_and_other_board(images):
    r = images
    first, second = [upload(r).json() for _ in range(2)]
    assert save(r, canvas_document(first["id"])).status_code == 200
    assert publish(r).status_code == 200
    assert save(r, canvas_document(second["id"]), revision=1).status_code == 200
    due_now(r)
    assert drain(r)["done"] == 0
    assert r.client.delete(first["url"], headers=r.headers["member"]).status_code == 409
    assert unpublish(r).status_code == 200
    due_now(r)
    assert drain(r)["done"] == 1
    assert r.client.get(second["url"], headers=r.headers["member"]).status_code == 200
    assert publish(r).status_code == 200
    other = r.client.post(
        "/api/v1/boards",
        headers=r.headers["owner"],
        json={**PAYLOAD, "slug": "publication-foreign"},
    ).json()
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    response = r.client.request(
        "DELETE",
        r.path,
        headers=r.headers["owner"],
        json={"expected_revision": revision(r), "confirm_slug": r.board["slug"]},
    )
    assert response.status_code == 204, response.text

    async def remaining():
        async with get_db() as db:
            for model in (
                Canvas,
                CanvasDocument,
                CanvasPublicationCounter,
                CanvasPublication,
                CanvasPublicationTag,
                CanvasAssetRef,
                Asset,
            ):
                assert (await db.scalars(select(model))).first() is None
            assert await db.get(Board, UUID(other["id"])) is not None
            assert await db.get(User, r.ids["member"]) is not None
            jobs = (await db.scalars(select(AssetDeletionOutbox))).all()
            assert any(job.reason == "board_deleted" for job in jobs)

    r.client.portal.call(remaining)
    assert drain(r)["done"] == 1


def test_fk_enabled_populated_sqlite_migration_preserves_parent_children_and_outbox(
    images, tmp_path, monkeypatch
):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert mutate(r, tag_ids=[tag(r, "마이그레이션 태그")["id"]]).status_code == 200
    clone = tmp_path / "publication-migration.db"
    with (
        sqlite3.connect(make_url(SETTINGS.DATABASE_URL).database) as source,
        sqlite3.connect(clone) as target,
    ):
        source.backup(target)
    url = f"sqlite+aiosqlite:///{clone}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    config = _build_alembic_config(url)
    engine = create_engine(f"sqlite:///{clone}")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
            config.attributes["connection"] = connection
            command.downgrade(config, "0028_canvas_tags")
            # A legacy publication-scope ref is also preserved, without making it public.
            connection.exec_driver_sql(
                "INSERT INTO canvas_asset_refs SELECT canvas_id,asset_id,'publication',board_id,asset_state FROM canvas_asset_refs WHERE scope='draft'"
            )
            connection.commit()
            tables = (
                "canvases",
                "canvas_documents",
                "assets",
                "canvas_asset_refs",
                "canvas_tags",
                "tags",
                "asset_deletion_outbox",
                "users",
                "boards",
            )

            def persisted():
                return {
                    table: connection.exec_driver_sql(
                        f'SELECT * FROM "{table}" ORDER BY rowid'
                    ).fetchall()
                    for table in tables
                }

            before = persisted()
            parent = connection.exec_driver_sql(
                "SELECT rootpage,sql FROM sqlite_schema WHERE name='canvases'"
            ).all()
            command.upgrade(config, "head")
            assert persisted() == before
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
            assert (
                connection.exec_driver_sql(
                    "SELECT rootpage,sql FROM sqlite_schema WHERE name='canvases'"
                ).all()
                == parent
            )
            connection.commit()
            with pytest.raises(RuntimeError, match="Publication history or references"):
                command.downgrade(config, "0028_canvas_tags")
            connection.rollback()
            connection.exec_driver_sql("DELETE FROM canvas_asset_refs WHERE scope='publication'")
            connection.commit()
            before = persisted()
            connection.commit()
            command.downgrade(config, "0028_canvas_tags")
            command.upgrade(config, "head")
            assert persisted() == before
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        engine.dispose()


def test_snapshot_tag_position_uniqueness_and_fk_constraints(images):
    r = images
    items = [tag(r, "첫 태그"), tag(r, "두 번째 태그")]
    assert mutate(r, tag_ids=[items[0]["id"]]).status_code == 200
    assert publish(r).status_code == 200

    async def reject():
        async with get_db() as db:
            db.add(
                CanvasPublicationTag(
                    canvas_id=r.canvas_id,
                    tag_id=UUID(items[1]["id"]),
                    name="두 번째 태그",
                    position=0,
                )
            )
            with pytest.raises(IntegrityError):
                await db.commit()
        async with get_db() as db:
            with pytest.raises(IntegrityError):
                await db.execute(delete(Tag).where(Tag.id == UUID(items[0]["id"])))
                await db.commit()

    r.client.portal.call(reject)


def test_optional_bearer_and_api_key_only_reads_never_substitute_for_membership(images):
    r = images
    image = upload(r).json()
    assert save(r, canvas_document(image["id"])).status_code == 200
    assert publish(r).status_code == 200
    issued = r.client.post(
        "/api/v1/api-keys", headers=r.headers["member"], json={"name": "publication-policy"}
    )
    assert issued.status_code == 200
    key = {"X-API-Key": issued.json()["api_key"]}
    paths = (r.canvas_path, r.canvas_path + "/document", image["url"])
    for path in paths:
        response = r.client.get(path, headers=key)
        assert (
            response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
        )
        assert r.client.get(path, headers=key, params={"view": "draft"}).status_code == 404
        rejected = r.client.get(path, headers={**key, "Authorization": "Bearer invalid"})
        assert rejected.status_code == 401 and rejected.json()["detail"]["error"] == "INVALID_TOKEN"
    for suffix, form in (
        ("publish", publication_form(r)),
        ("unpublish", {"expected_publication_revision": 1}),
    ):
        response = r.client.post(r.canvas_path + "/" + suffix, headers=key, json=form)
        assert response.status_code == 401
    assert mutate(r, visibility="members").status_code == 200
    for path in paths:
        assert r.client.get(path, headers=key).status_code == 404
        assert (
            r.client.get(
                path, headers=r.headers["member"], params={"view": "publication"}
            ).status_code
            == 200
        )

    async def deactivate():
        async with get_db() as db:
            (await db.get(User, r.ids["member"])).is_active = False
            await db.commit()

    r.client.portal.call(deactivate)
    for path in paths:
        rejected = r.client.get(path, headers=r.headers["member"])
        assert (
            rejected.status_code == 404 and rejected.json()["detail"]["error"] == "USER_NOT_FOUND"
        )
