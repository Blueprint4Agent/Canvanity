"""Real HTTP, SQLite and private local files exercise upload/cleanup failure boundaries."""

import asyncio
from datetime import UTC, datetime, timedelta
from functools import partial
from io import BytesIO
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.error.asset_exception import AssetErrorCode, AssetException
from app.core.object_storage import StorageError, StorageErrorCode
from app.core.object_storage.identity import StorageLocation
from app.models.asset import Asset, AssetDeletionOutbox, AssetRepository, CanvasAssetRef
from app.models.board import BoardMember
from app.models.user import User
from app.services.asset import AssetService
from app.services.asset_cleanup import AssetCleanupService
from app.services.board_permission import BoardPermissionService
from app.services.canvas_access import CanvasAccessService
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import (
    board_write,
    create,
    draft as draft,
    mutate,
    promote,
)
from tests.unit.services.test_canvas_image import encoded_image

pytestmark = pytest.mark.primary_data


@pytest.fixture
def images(draft):
    r = draft
    r.assets_path = r.canvas_path + "/assets"
    r.canvas_id = UUID(r.canvas["canvas"]["id"])
    r.storage = r.client.app.state.object_storage
    r.location = r.client.app.state.object_storage_location
    r.repository = AssetRepository()
    r.access = CanvasAccessService(BoardPermissionService())
    r.cleanup = AssetCleanupService(r.repository, r.storage, r.location)
    return r


def upload(r, *, actor="member", payload=None, path=None):
    return r.client.post(
        path or r.assets_path,
        headers=r.headers[actor],
        files={
            "file": (
                "untrusted.html",
                payload if payload is not None else encoded_image(),
                "text/html",
            )
        },
    )


def stored(r):
    async def read():
        async with get_db() as db:
            return list(
                (await db.scalars(select(Asset).order_by(Asset.created_at, Asset.id))).all()
            ), list(
                (
                    await db.scalars(
                        select(AssetDeletionOutbox).order_by(
                            AssetDeletionOutbox.created_at, AssetDeletionOutbox.id
                        )
                    )
                ).all()
            )

    return r.client.portal.call(read)


def due_now(r, *, expire_upload=True):
    async def age():
        async with get_db() as db:
            past = datetime.now(UTC) - timedelta(seconds=1)
            for job in (await db.scalars(select(AssetDeletionOutbox))).all():
                job.available_at = past
            if expire_upload:
                for asset in (await db.scalars(select(Asset))).all():
                    asset.upload_deadline = past
            await db.commit()

    r.client.portal.call(age)


def drain(r, cleanup=None):
    return r.client.portal.call((cleanup or r.cleanup).drain)


def references(r, asset_ids, *, scope="draft", canvas_id=None):
    async def change():
        async with r.repository.transaction() as tx:
            _, _, canvas = await r.access.context(
                tx.context, r.ids["member"], canvas_id or r.canvas_id, write=True
            )
            await tx.replace_refs(canvas, set(asset_ids), scope=scope)

    return r.client.portal.call(change)


def test_private_normalized_image_lifecycle_and_deferred_idempotent_cleanup(images):
    r = images
    response = upload(r)
    assert response.status_code == 201, response.text
    result = response.json()
    assert set(result) == {
        "id",
        "canvas_id",
        "content_type",
        "byte_size",
        "width",
        "height",
        "frame_count",
        "state",
        "expires_at",
        "created_at",
        "url",
    }
    assert result["state"] == "ready" and result["expires_at"]
    url = response.headers["location"]
    assert url == result["url"]
    photo = r.client.get(url, headers=r.headers["member"])
    assert photo.status_code == 200 and photo.headers["cache-control"] == "private, no-store"
    with Image.open(BytesIO(photo.content)) as image:
        assert image.format == "WEBP" and not image.getexif() and image.size == (8, 12)
    assert len(photo.content) == result["byte_size"]
    assets, jobs = stored(r)
    assert len(assets) == len(jobs) == 1 and jobs[0].reason == "unused_upload"
    assert drain(r)["done"] == 0  # 24-hour grace, no synchronous deletion.
    for actor in ("owner", "admin", "moderator", "peer", "outsider"):
        assert r.client.get(url, headers=r.headers[actor]).status_code == 404
        assert r.client.delete(url, headers=r.headers[actor]).status_code == 404
        assert upload(r, actor=actor).status_code == 404
    assert r.client.get(url).status_code == 401
    other = create(r).headers["location"]
    assert (
        r.client.get(other + "/assets/" + result["id"], headers=r.headers["member"]).status_code
        == 404
    )
    assert r.client.delete(url, headers=r.headers["member"]).status_code == 204
    assert r.client.delete(url, headers=r.headers["member"]).status_code == 204
    assert r.client.get(url, headers=r.headers["member"]).status_code == 404
    assert r.client.portal.call(r.storage.stat, assets[0].object_key).size > 0
    assert drain(r) == {"done": 1, "failed": 0, "skipped": 0}
    assert stored(r)[0] == [] and stored(r)[1][0].state == "done"
    assert drain(r)["done"] == 0
    with pytest.raises(StorageError):
        r.client.portal.call(r.storage.stat, assets[0].object_key)


@pytest.mark.parametrize("payload,status", [(b"<svg/>", 422), (b"x" * (8 * 1024 * 1024 + 1), 413)])
def test_invalid_or_oversized_upload_creates_no_reservation_or_file(images, payload, status):
    r = images
    assert upload(r, payload=payload).status_code == status
    assert stored(r) == ([], [])


def test_current_grade_member_and_board_states_are_rechecked(images):
    r = images
    response = upload(r)
    url = response.json()["url"]
    promote(r, grade=0)
    assert upload(r).status_code == 403
    assert r.client.get(url, headers=r.headers["member"]).status_code == 200
    assert r.client.delete(url, headers=r.headers["member"]).status_code == 204
    promote(r)
    url = upload(r).json()["url"]
    assert mutate(r, "DELETE").status_code == 204
    assert r.client.get(url, headers=r.headers["member"]).status_code == 200
    assert upload(r).status_code == 409
    assert mutate(r, "POST", suffix="/restore").status_code == 200
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    assert r.client.get(url, headers=r.headers["member"]).status_code == 200
    assert (
        upload(r).status_code
        == r.client.delete(url, headers=r.headers["member"]).status_code
        == 403
    )


@pytest.mark.parametrize("status", ["pending", "suspended", "banned", "left"])
def test_membership_loss_hides_existing_image(images, status):
    r = images
    url = upload(r).json()["url"]

    async def revoke():
        async with get_db() as db:
            member = await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))
            if status == "left":
                await db.delete(member)
            else:
                member.status = status
            await db.commit()

    r.client.portal.call(revoke)
    assert r.client.get(url, headers=r.headers["member"]).status_code == 404
    assert upload(r).status_code == 404


def test_draft_and_publication_references_both_protect_until_last_reference_is_removed(images):
    r = images
    result = upload(r).json()
    asset_id = UUID(result["id"])
    references(r, [asset_id])
    references(r, [asset_id], scope="publication")
    assert stored(r)[0][0].expires_at is None
    assert (
        r.client.portal.call(r.repository.inventory) == []
    )  # Normal live references need no operator action.
    assert r.client.delete(result["url"], headers=r.headers["member"]).status_code == 409
    due_now(r)
    assert drain(r)["done"] == 0
    references(r, [], scope="draft")
    assert r.client.delete(result["url"], headers=r.headers["member"]).status_code == 409
    other = create(r).json()["canvas"]["id"]
    with pytest.raises(AssetException) as caught:
        references(r, [asset_id], canvas_id=UUID(other))
    assert caught.value.code == AssetErrorCode.INVALID_REFERENCE.code
    references(r, [], scope="publication")
    assert stored(r)[0][0].expires_at is not None
    due_now(r)
    assert drain(r)["done"] == 1


@pytest.mark.parametrize(
    "when", ["before_put", "after_put", "finalize", "ambiguous_commit", "revoked"]
)
def test_failures_preserve_durable_cleanup_and_ambiguous_success(images, monkeypatch, when):
    r = images
    original_put, original_commit = r.storage.put, AsyncSession.commit
    commits = 0

    async def put(key, data, content_type):
        if when == "before_put":
            raise StorageError(StorageErrorCode.UNAVAILABLE)
        result = await original_put(key, data, content_type)
        if when == "after_put":
            raise StorageError(StorageErrorCode.UNAVAILABLE)
        if when == "revoked":
            async with get_db() as db:
                (
                    await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))
                ).status = "suspended"
                await db.commit()
        return result

    async def commit(db):
        nonlocal commits
        commits += 1
        if commits == 2 and when == "finalize":
            raise SQLAlchemyError("unconfirmed finalization")
        await original_commit(db)
        if commits == 2 and when == "ambiguous_commit":
            raise SQLAlchemyError("connection lost after commit")

    monkeypatch.setattr(r.storage, "put", put)
    if when in {"finalize", "ambiguous_commit"}:
        monkeypatch.setattr(AsyncSession, "commit", commit)
    result = upload(r)
    assert result.status_code == (404 if when == "revoked" else 503), result.text
    assets, jobs = stored(r)
    assert len(assets) == len(jobs) == 1
    if when == "ambiguous_commit":
        assert assets[0].state == "ready" and jobs[0].reason == "unused_upload"
        url = r.assets_path + "/" + str(assets[0].id)
        assert r.client.get(url, headers=r.headers["member"]).status_code == 200
    else:
        assert (
            assets[0].state == "deleting"
            and jobs[0].state == "pending"
            and jobs[0].reason == "upload_failed"
        )
        assert drain(r)["done"] == 0  # Unknown remote puts retain their reservation grace.
        due_now(r)
        assert drain(r)["done"] == 1
        assert stored(r)[0] == []


def test_reservation_failure_never_calls_storage_and_cancelled_put_remains_recoverable(
    images, monkeypatch
):
    r = images
    original_put = r.storage.put
    put = AsyncMock(wraps=original_put)
    monkeypatch.setattr(r.storage, "put", put)
    with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("reservation failed")):
        assert upload(r).status_code == 503
    put.assert_not_awaited()
    assert stored(r) == ([], [])

    async def cancelled(key, data, content_type):
        await original_put(key, data, content_type)
        raise asyncio.CancelledError()

    monkeypatch.setattr(r.storage, "put", cancelled)

    async def invoke():
        async def chunks():
            yield encoded_image()

        with pytest.raises(asyncio.CancelledError):
            await AssetService(r.access, r.repository, r.storage, r.location).upload(
                r.ids["member"], r.canvas_id, chunks()
            )

    r.client.portal.call(invoke)
    assert stored(r)[1][0].reason == "upload_failed"
    due_now(r)
    assert drain(r)["done"] == 1


def test_cleanup_retry_backoff_limit_lease_fencing_and_storage_binding(images, monkeypatch):
    r = images
    result = upload(r).json()
    assert r.client.delete(result["url"], headers=r.headers["member"]).status_code == 204
    job = stored(r)[1][0]
    wrong = AssetCleanupService(r.repository, r.storage, StorageLocation("different", {}))
    assert drain(r, wrong)["skipped"] == 1 and stored(r)[1][0].last_error == "storage_mismatch"
    assert r.client.portal.call(r.repository.retry, job.id)
    first = r.client.portal.call(r.repository.claim, job.id, r.location.fingerprint)
    assert (
        first and r.client.portal.call(r.repository.claim, job.id, r.location.fingerprint) is None
    )
    assert not r.client.portal.call(
        r.repository.retry, job.id
    )  # Live lease cannot be stolen manually.
    due_now(r)
    second = r.client.portal.call(r.repository.claim, job.id, r.location.fingerprint)
    assert second.token != first.token
    assert not r.client.portal.call(r.repository.finish, first)
    assert r.client.portal.call(partial(r.repository.finish, second, error="unavailable"))
    assert stored(r)[1][0].attempts == 2 and drain(r)["done"] == 0
    original_delete = r.storage.delete
    monkeypatch.setattr(
        r.storage, "delete", AsyncMock(side_effect=StorageError(StorageErrorCode.UNAVAILABLE))
    )
    for attempt in range(3, 6):
        due_now(r)
        assert drain(r)["failed"] == 1
        assert stored(r)[1][0].attempts == attempt
    assert stored(r)[1][0].state == "dead"
    assert r.client.portal.call(r.repository.retry, job.id)
    monkeypatch.setattr(r.storage, "delete", original_delete)
    assert drain(r)["done"] == 1
    # A late put completion can reopen even a completed deletion tombstone.
    r.client.portal.call(r.storage.put, job.object_key, b"late-upload", "image/webp")
    r.client.portal.call(r.repository.upload_failed, UUID(result["id"]))
    assert stored(r)[1][0].state == "pending"
    due_now(r)
    assert drain(r)["done"] == 1


def test_live_profile_reference_and_invalid_namespace_never_delete_files(images, monkeypatch):
    r = images
    result = upload(r).json()
    asset, job = stored(r)[0][0], stored(r)[1][0]

    async def profile_ref(value):
        async with get_db() as db:
            (await db.get(User, r.ids["owner"])).profile_photo = value
            await db.commit()

    r.client.portal.call(profile_ref, {"key": asset.object_key, "storage": r.location.fingerprint})
    due_now(r)
    assert drain(r)["skipped"] == 1
    assert stored(r)[1][0].state == "protected"
    assert r.client.get(result["url"], headers=r.headers["member"]).status_code == 200
    r.client.portal.call(profile_ref, None)
    r.client.portal.call(r.repository.retry, job.id)

    async def invalid_key():
        async with get_db() as db:
            (
                await db.get(AssetDeletionOutbox, job.id)
            ).object_key = "profile-photos/1/untouchable.webp"
            await db.commit()

    r.client.portal.call(invalid_key)
    delete = AsyncMock(wraps=r.storage.delete)
    monkeypatch.setattr(r.storage, "delete", delete)
    assert drain(r)["failed"] == 1 and stored(r)[1][0].last_error == "invalid_key"
    delete.assert_not_awaited()


def test_read_uses_frozen_storage_location_and_rejects_tampered_objects(
    images, monkeypatch, tmp_path
):
    r = images
    result = upload(r).json()
    from app.core.config.settings import SETTINGS

    monkeypatch.setattr(SETTINGS, "OBJECT_STORAGE_LOCAL_ROOT", tmp_path / "other-config")
    assert r.client.get(result["url"], headers=r.headers["member"]).status_code == 200
    asset = stored(r)[0][0]
    r.client.portal.call(r.storage.put, asset.object_key, b"x" * asset.byte_size, "image/webp")
    response = r.client.get(result["url"], headers=r.headers["member"])
    assert response.status_code == 503 and response.json()["detail"]["error"] == "ASSET_UNAVAILABLE"


def test_board_delete_rolls_back_intent_or_commits_durable_parent_independent_cleanup(images):
    r = images
    result = upload(r).json()
    references(r, [UUID(result["id"])], scope="publication")
    assert board_write(r, "PATCH", r.path, status="archived").status_code == 200

    def remove_board():
        from tests.integration.api.v1.board.test_board_member_administration import revision

        return r.client.request(
            "DELETE",
            r.path,
            headers=r.headers["owner"],
            json={"expected_revision": revision(r), "confirm_slug": r.board["slug"]},
        )

    with patch.object(AsyncSession, "commit", side_effect=SQLAlchemyError("delete failed")):
        assert remove_board().status_code == 503
    assert r.client.get(result["url"], headers=r.headers["member"]).status_code == 200
    assert stored(r)[1][0].state == "protected"
    assert remove_board().status_code == 204
    assert stored(r)[0] == []
    assert stored(r)[1][0].reason == "board_deleted"
    assert drain(r)["done"] == 1


def test_quota_and_ready_reference_foreign_key(images, monkeypatch):
    r = images
    monkeypatch.setattr("app.models.asset.MAX_ASSETS_PER_CANVAS", 1)
    result = upload(r).json()
    assert upload(r).status_code == 409
    references(r, [UUID(result["id"])])

    async def break_reference():
        async with get_db() as db:
            (await db.get(Asset, UUID(result["id"]))).state = "deleting"
            await db.commit()

    with pytest.raises(SQLAlchemyError):
        r.client.portal.call(break_reference)
    references(r, [])
    assert r.client.delete(result["url"], headers=r.headers["member"]).status_code == 204

    async def attach_deleting():
        async with get_db() as db:
            db.add(
                CanvasAssetRef(
                    canvas_id=r.canvas_id,
                    board_id=UUID(r.board["id"]),
                    asset_id=UUID(result["id"]),
                    scope="draft",
                )
            )
            await db.commit()

    with pytest.raises(SQLAlchemyError):
        r.client.portal.call(attach_deleting)
    assert drain(r)["done"] == 1
    assert upload(r).status_code == 201


def test_populated_sqlite_migration_preserves_document_and_refuses_losing_cleanup(
    images, tmp_path, monkeypatch
):
    import sqlite3

    from sqlalchemy.engine import make_url

    from alembic import command
    from app.core.config.settings import SETTINGS
    from app.core.db.migrations import _build_alembic_config

    r = images
    assert upload(r).status_code == 201
    clone = tmp_path / "migration-copy.db"
    with (
        sqlite3.connect(make_url(SETTINGS.DATABASE_URL).database) as source,
        sqlite3.connect(clone) as target,
    ):
        source.backup(target)
        before = target.execute(
            "SELECT canvas_id,document,revision FROM canvas_documents"
        ).fetchall()
    url = f"sqlite+aiosqlite:///{clone}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    config = _build_alembic_config(url)
    with pytest.raises(RuntimeError, match="Drain asset cleanup"):
        command.downgrade(config, "0026_canvas_drafts")
    with sqlite3.connect(clone) as db:
        assert (
            db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            == "0027_canvas_assets"
        )
        db.execute("DELETE FROM assets")
        db.execute("UPDATE asset_deletion_outbox SET state='done'")
    command.downgrade(config, "0026_canvas_drafts")
    command.upgrade(config, "head")
    with sqlite3.connect(clone) as db:
        assert (
            db.execute("SELECT canvas_id,document,revision FROM canvas_documents").fetchall()
            == before
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_standalone_cleanup_cli_uses_same_isolated_database_and_storage(images):
    import json
    import os
    import subprocess
    import sys

    from sqlalchemy.engine import make_url

    from app.core.config.settings import SETTINGS

    r = images
    result = upload(r).json()
    assert r.client.delete(result["url"], headers=r.headers["member"]).status_code == 204
    completed = subprocess.run(
        [sys.executable, "-m", "app.manage_asset_cleanup", "--limit", "5"],
        env={
            **os.environ,
            "DB_DRIVER": "sqlite+aiosqlite",
            "DB_NAME": make_url(SETTINGS.DATABASE_URL).database,
            "OBJECT_STORAGE_PROVIDER": "local",
            "OBJECT_STORAGE_LOCAL_ROOT": str(SETTINGS.OBJECT_STORAGE_LOCAL_ROOT),
            "TRACING_ENABLED": "false",
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    report = json.loads(completed.stdout.strip().splitlines()[-1])
    assert report == {"done": 1, "failed": 0, "skipped": 0, "attention": []}
    assert stored(r)[0] == [] and stored(r)[1][0].state == "done"
