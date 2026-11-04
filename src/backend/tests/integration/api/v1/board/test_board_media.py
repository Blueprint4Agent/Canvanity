"""Real SQLite HTTP and temporary private files cover Board media lifecycle boundaries."""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from functools import partial
from io import BytesIO
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.object_storage import StorageError, StorageErrorCode
from app.models.asset import Asset, AssetDeletionOutbox, AssetRepository, CanvasAssetRef
from app.models.board import (
    Board,
    BoardDeleteForm,
    BoardMember,
    BoardMemberAudit,
    BoardRepository,
)
from app.models.board_media import (
    BoardMediaAsset,
    BoardMediaChangeForm,
    BoardMediaRef,
    BoardMediaRepository,
    BoardMediaTransaction,
)
from app.models.user import User
from app.services.asset_cleanup import AssetCleanupService
from app.services.board import BoardService
from app.services.board_media import BoardMediaService
from app.services.board_permission import BoardPermissionService
from tests.integration.api.v1.board.test_board_member_administration import (
    revision,
    roster as roster,
    window,
)
from tests.unit.services.test_canvas_image import encoded_image

pytestmark = pytest.mark.primary_data


@pytest.fixture
def media(roster):
    r = roster
    r.board_id = UUID(r.board["id"])
    r.storage = r.client.app.state.object_storage
    r.location = r.client.app.state.object_storage_location
    r.repository = BoardMediaRepository()
    r.cleanup_repository = AssetRepository()
    r.cleanup = AssetCleanupService(r.cleanup_repository, r.storage, r.location)
    r.service = BoardMediaService(BoardPermissionService(), r.repository, r.storage, r.location)
    return r


def upload(r, slot="cover", actor="owner", *, expected=None, payload=None):
    return r.client.put(
        r.path + f"/media/{slot}",
        headers=r.headers[actor],
        data={
            "expected_revision": str(revision(r) if expected is None else expected),
            "reason": "보드 이미지 변경",
        },
        files={
            "file": (
                "untrusted.svg",
                encoded_image() if payload is None else payload,
                "image/svg+xml",
            )
        },
    )


def remove(r, slot="cover", *, expected=None, actor="owner"):
    return r.client.request(
        "DELETE",
        r.path + f"/media/{slot}",
        headers=r.headers[actor],
        json={
            "expected_revision": revision(r) if expected is None else expected,
            "reason": "이미지 해제",
        },
    )


def stored(r):
    async def read():
        async with get_db() as db:
            return tuple(
                [
                    list(
                        (
                            await db.scalars(
                                select(model).order_by(*model.__table__.primary_key.columns)
                            )
                        ).all()
                    )
                    for model in (
                        BoardMediaAsset,
                        BoardMediaRef,
                        AssetDeletionOutbox,
                        BoardMemberAudit,
                    )
                ]
            )

    return r.client.portal.call(read)


def due(r):
    async def age():
        async with get_db() as db:
            past = datetime.now(UTC) - timedelta(seconds=1)
            for job in (await db.scalars(select(AssetDeletionOutbox))).all():
                job.available_at = past
            for asset in (await db.scalars(select(BoardMediaAsset))).all():
                asset.upload_deadline = past
            await db.commit()

    r.client.portal.call(age)


def drain(r):
    return r.client.portal.call(r.cleanup.drain)


def test_real_files_current_versions_projection_cas_and_deferred_cleanup(media):
    r = media
    before = revision(r)
    assert remove(r).json() == {
        "board_id": str(r.board_id),
        "slot": "cover",
        "media": None,
        "board_revision": before,
        "changed": False,
    }
    response = upload(r)
    assert response.status_code == 200, response.text
    cover = response.json()["media"]
    assert response.json()["board_revision"] == before + 1
    photo = r.client.get(cover["url"])
    assert photo.status_code == 200 and photo.headers["cache-control"] == "private, no-store"
    assert photo.headers["x-content-type-options"] == "nosniff"
    with Image.open(BytesIO(photo.content)) as image:
        assert image.format == "WEBP" and image.size == (8, 12) and not image.getexif()
    assert len(photo.content) == cover["byte_size"]
    assert set(cover) == {
        "id",
        "content_type",
        "byte_size",
        "width",
        "height",
        "frame_count",
        "created_at",
        "url",
    }
    assert upload(r, "avatar", actor="admin").status_code == 200
    assets, refs, jobs, audits = stored(r)
    assert len(assets) == len(refs) == len(jobs) == 2
    assert all(j.state == "protected" for j in jobs)
    assert all(a.storage_location == r.location.descriptor for a in assets)
    assert assets[0].sha256 == hashlib.sha256(photo.content).hexdigest()
    home = r.client.get(r.path + "/home", headers=r.headers["owner"]).json()
    assert home["can_manage_media"] and home["board"]["cover"] == cover
    for target in (r.path, "/api/v1/boards/by-slug/" + r.board["slug"]):
        assert r.client.get(target).json()["board"] == home["board"]
    listed = r.client.get("/api/v1/boards").json()["items"][0]
    assert listed == home["board"] and listed["cover_asset_id"] == cover["id"]
    assert not r.client.get(r.path + "/home").json()["can_manage_media"]
    # Only an actual official cover widget receives the selected cover; document remains source-free.
    layout = r.client.get(r.path + "/layout", headers=r.headers["owner"]).json()
    document = layout["document"]
    document["widgets"].append(
        {
            "id": "media-cover",
            "type": "board_cover",
            "position": {"x": 1, "y": 1},
            "size": {"width": 100, "height": 100},
        }
    )
    assert (
        r.client.put(
            r.path + "/layout",
            headers=r.headers["owner"],
            json={
                "expected_revision": layout["layout_revision"],
                "reason": "커버 추가",
                "document": document,
            },
        ).status_code
        == 200
    )
    rendered = r.client.get(r.path + "/home").json()
    assert next(w for w in rendered["widget_data"] if w["id"] == "media-cover")["media"] == cover
    assert upload(r, expected=before).status_code == 409
    assert remove(r, expected=before).status_code == 409
    replaced = upload(r).json()["media"]
    assert replaced["id"] != cover["id"] and r.client.get(cover["url"]).status_code == 404
    assert r.client.get(replaced["url"]).status_code == 200
    assert drain(r) == {"done": 1, "failed": 0, "skipped": 0}
    assert remove(r).json()["changed"]
    assert remove(r).json()["changed"] is False
    assert r.client.get(replaced["url"]).status_code == 404
    assert drain(r)["done"] == 1
    audit = r.client.get(
        r.path + "/member-audit", headers=r.headers["owner"], params=window()
    ).json()["items"]
    changes = [a for a in audit if a["action"] == "media_changed"]
    assert len(changes) == 4
    for change in changes:
        assert change["before"] is change["after"] is None
        assert set(change["media_change"]) == {
            "slot",
            "before_asset_id",
            "after_asset_id",
            "before_revision",
            "after_revision",
        }
    assert (
        r.client.get(r.path + "/layout", headers=r.headers["owner"]).json()["document"] == document
    )


@pytest.mark.parametrize("actor", ["moderator", "member", "peer", "outsider"])
def test_only_current_owner_admin_can_change_regardless_grade_or_global_admin(media, actor):
    r = media
    assert upload(r, actor=actor).status_code == 403
    assert remove(r, actor=actor).status_code == 403
    assert stored(r)[:3] == ([], [], [])


@pytest.mark.parametrize(
    "status", ["private", "archived", "suspended", "banned", "left", "inactive"]
)
def test_current_read_policy_and_version_non_exposure(media, status):
    r = media
    image = upload(r).json()["media"]

    async def change():
        async with get_db() as db:
            board = await db.get(Board, r.board_id)
            member = await db.get(BoardMember, (r.board_id, r.ids["admin"]))
            if status == "private":
                board.visibility, board.join_policy = "private", "invite"
            elif status in {"archived", "suspended"}:
                board.status = status
            elif status == "left":
                board.visibility, board.join_policy = "private", "invite"
                await db.delete(member)
            elif status == "inactive":
                (await db.get(User, r.ids["admin"])).is_active = False
            else:
                member.status = status
            await db.commit()

    r.client.portal.call(change)
    expected = 200 if status in {"private", "archived"} else 404
    assert r.client.get(image["url"], headers=r.headers["admin"]).status_code == expected
    if status == "private":
        assert r.client.get(image["url"]).status_code == 404
    if status == "archived":
        assert upload(r).status_code == 403 and remove(r).status_code == 403
    assert r.client.get(image["url"].replace("/cover/", "/avatar/")).status_code == 404
    assert r.client.get(image["url"].replace(str(r.board_id), str(uuid4()))).status_code == 404


@pytest.mark.parametrize(
    "payload,expected", [(b"<svg/>", 422), (b"GIF89a", 422), (b"x" * (8 * 1024 * 1024 + 1), 413)]
)
def test_invalid_images_never_reserve_or_write(media, payload, expected):
    assert upload(media, payload=payload).status_code == expected
    assert stored(media)[:3] == ([], [], [])


@pytest.mark.parametrize(
    "when",
    [
        "put",
        "after_put",
        "revoked",
        "inactive",
        "settings",
        "finalize",
        "ambiguous_commit",
        "cancelled",
    ],
)
def test_failure_compensation_preserves_original_selection_and_confirmed_ready(
    media, monkeypatch, when
):
    r = media
    original_put, original_commit = r.storage.put, AsyncSession.commit
    commits = 0

    async def put(key, data, content_type):
        if when == "put":
            raise StorageError(StorageErrorCode.UNAVAILABLE)
        await original_put(key, data, content_type)
        if when == "after_put":
            raise StorageError(StorageErrorCode.UNAVAILABLE)
        if when == "cancelled":
            raise asyncio.CancelledError()
        if when in {"revoked", "inactive", "settings"}:
            async with get_db() as db:
                if when == "revoked":
                    (await db.get(BoardMember, (r.board_id, r.ids["admin"]))).role = "member"
                elif when == "inactive":
                    (await db.get(User, r.ids["admin"])).is_active = False
                else:
                    (await db.get(Board, r.board_id)).revision += 1
                await db.commit()

    async def commit(db):
        nonlocal commits
        commits += 1
        if commits == 3 and when == "finalize":
            raise SQLAlchemyError("controlled unconfirmed finalization")
        await original_commit(db)
        if commits == 3 and when == "ambiguous_commit":
            raise SQLAlchemyError("controlled lost commit acknowledgement")

    monkeypatch.setattr(r.storage, "put", put)
    if when in {"finalize", "ambiguous_commit"}:
        monkeypatch.setattr(AsyncSession, "commit", commit)
    if when == "cancelled":

        async def invoke():
            async def chunks():
                yield encoded_image()

            with pytest.raises(asyncio.CancelledError):
                await r.service.upload(
                    r.ids["admin"],
                    r.board_id,
                    "cover",
                    BoardMediaChangeForm(expected_revision=revision_value, reason="취소"),
                    chunks(),
                )

        revision_value = revision(r)
        r.client.portal.call(invoke)
    else:
        result = upload(r, actor="admin")
        assert result.status_code == {"revoked": 403, "inactive": 404, "settings": 409}.get(
            when, 503
        ), result.text
    assets, refs, jobs, audits = stored(r)
    assert len(assets) == len(jobs) == 1
    if when == "ambiguous_commit":
        assert assets[0].state == "ready" and len(refs) == 1 and jobs[0].state == "protected"
        assert r.client.get(r.path + f"/media/cover/{assets[0].id}").status_code == 200
    else:
        assert not refs and assets[0].state == "deleting" and jobs[0].reason == "upload_failed"
        assert drain(r)["done"] == 0
        due(r)
        assert drain(r)["done"] == 1


def test_limits_saturation_and_database_ready_same_board_slot_constraints(media, monkeypatch):
    r = media
    first = upload(r).json()["media"]
    monkeypatch.setattr("app.models.board_media.MAX_BOARD_MEDIA_ASSETS", 1)
    assert upload(r).status_code == 409

    async def invalid(kind):
        async with get_db() as db:
            if kind == "state":
                (await db.get(BoardMediaAsset, UUID(first["id"]))).state = "deleting"
            else:
                db.add(
                    BoardMediaRef(
                        board_id=r.board_id,
                        slot="avatar",
                        asset_id=UUID(first["id"]),
                        asset_state="pending" if kind == "ready" else "ready",
                    )
                )
            await db.commit()

    for kind in ("state", "ready", "slot"):
        with pytest.raises(SQLAlchemyError):
            r.client.portal.call(invalid, kind)

    async def saturate():
        async with get_db() as db:
            (await db.get(Board, r.board_id)).revision = 2**31 - 1
            await db.commit()

    r.client.portal.call(saturate)
    assert upload(r).status_code == 409 and remove(r).status_code == 409
    assert remove(r, "avatar").json()["changed"] is False


def test_read_integrity_location_and_policy_recheck_after_io(media, monkeypatch):
    r = media
    image = upload(r).json()["media"]
    asset = stored(r)[0][0]
    original_get = r.storage.get

    async def revoke_after_get(key):
        data = await original_get(key)
        async with get_db() as db:
            (await db.get(Board, r.board_id)).status = "suspended"
            await db.commit()
        return data

    monkeypatch.setattr(r.storage, "get", revoke_after_get)
    assert r.client.get(image["url"]).status_code == 404
    monkeypatch.setattr(r.storage, "get", original_get)

    async def restore():
        async with get_db() as db:
            (await db.get(Board, r.board_id)).status = "active"
            await db.commit()

    r.client.portal.call(restore)
    r.client.portal.call(r.storage.put, asset.object_key, b"x" * asset.byte_size, "image/webp")
    assert r.client.get(image["url"]).status_code == 503


def test_delete_board_rollback_pending_late_put_and_tombstone_reopen(media, monkeypatch):
    r = media
    original_put = r.storage.put

    async def delete_during_put(key, data, content_type):
        await original_put(key, data, content_type)
        async with get_db() as db:
            (await db.get(Board, r.board_id)).status = "archived"
            await db.commit()
        await BoardService(BoardPermissionService(), BoardRepository()).delete_board(
            r.ids["owner"],
            r.board_id,
            BoardDeleteForm(expected_revision=expected, confirm_slug=r.board["slug"]),
        )

    expected = revision(r)
    monkeypatch.setattr(r.storage, "put", delete_during_put)
    assert upload(r, expected=expected).status_code == 404
    assert stored(r)[0] == [] and stored(r)[1] == []
    job = stored(r)[2][0]
    assert job.state == "pending"
    assert drain(r)["done"] == 0
    due(r)
    assert drain(r)["done"] == 1
    awaitable = partial(original_put, job.object_key, b"late", "image/webp")
    r.client.portal.call(awaitable)
    r.client.portal.call(r.repository.upload_failed, job.asset_id)
    assert stored(r)[2][0].state == "pending"
    due(r)
    assert drain(r)["done"] == 1


def test_cross_registry_same_uuid_profile_and_invalid_location_protect_cleanup(media):
    r = media
    assert upload(r).status_code == 200
    asset = stored(r)[0][0]
    assert remove(r).status_code == 200

    async def protect():
        async with get_db() as db:
            (await db.get(User, r.ids["owner"])).profile_photo = {
                "key": asset.object_key,
                "storage": asset.storage_fingerprint,
            }
            await db.commit()

    r.client.portal.call(protect)
    assert drain(r)["skipped"] == 1 and stored(r)[2][0].state == "protected"

    async def corrupt():
        async with get_db() as db:
            (await db.get(User, r.ids["owner"])).profile_photo = None
            job = await db.get(AssetDeletionOutbox, stored_job_id)
            job.storage_location = {"provider": "local", "root": "/wrong"}
            await db.commit()

    stored_job_id = stored(r)[2][0].id
    r.client.portal.call(corrupt)
    r.client.portal.call(r.cleanup_repository.retry, stored_job_id)
    assert drain(r)["skipped"] == 1 and stored(r)[2][0].last_error == "storage_mismatch"
    assert r.client.portal.call(r.storage.stat, asset.object_key).size > 0


@pytest.mark.parametrize("same_key", [True, False])
def test_same_uuid_in_other_registry_protects_only_matching_object_key(media, same_key):
    r = media
    assert upload(r).status_code == 200
    asset = stored(r)[0][0]
    shelf = r.client.get(r.path + "/home").json()["shelves"][0]["id"]
    canvas = r.client.post(
        r.path + "/canvases",
        headers=r.headers["owner"],
        json={"shelf_id": shelf, "title": "별도 Canvas"},
    ).json()["canvas"]["id"]

    async def add():
        async with get_db() as db:
            db.add(
                Asset(
                    id=asset.id,
                    board_id=r.board_id,
                    canvas_id=UUID(canvas),
                    owner_id=r.ids["owner"],
                    object_key=asset.object_key
                    if same_key
                    else f"canvas-assets/{asset.id}/{uuid4().hex}.webp",
                    storage_fingerprint=asset.storage_fingerprint,
                    storage_location=asset.storage_location,
                    byte_size=asset.byte_size,
                    width=asset.width,
                    height=asset.height,
                    frame_count=asset.frame_count,
                    sha256=asset.sha256,
                    state="ready",
                    upload_deadline=asset.upload_deadline,
                )
            )
            await db.flush()
            db.add(
                CanvasAssetRef(
                    board_id=r.board_id, canvas_id=UUID(canvas), asset_id=asset.id, scope="draft"
                )
            )
            await db.commit()

    r.client.portal.call(add)
    assert remove(r).status_code == 200
    assert drain(r)["skipped" if same_key else "done"] == 1

    async def preserved():
        async with get_db() as db:
            assert await db.get(Asset, asset.id) is not None
            assert await db.get(CanvasAssetRef, (UUID(canvas), asset.id, "draft")) is not None

    r.client.portal.call(preserved)


def test_uploader_deletion_and_ownership_transfer_keep_community_media(media):
    r = media
    image = upload(r, actor="admin").json()["media"]
    assert (
        r.client.post(
            r.path + "/ownership-transfer",
            headers=r.headers["owner"],
            json={
                "expected_revision": revision(r),
                "reason": "소유권 이전",
                "target_user_id": r.ids["peer"],
            },
        ).status_code
        == 200
    )

    async def delete_uploader():
        async with get_db() as db:
            await db.execute(delete(User).where(User.id == r.ids["admin"]))
            await db.commit()

    r.client.portal.call(delete_uploader)
    assert stored(r)[0][0].owner_id is None
    assert r.client.get(image["url"]).status_code == 200
    due(r)
    assert drain(r)["done"] == 0


def test_board_media_cleanup_cli_uses_isolated_database_and_files(media):
    import json
    import os
    import subprocess
    import sys

    from sqlalchemy.engine import make_url

    from app.core.config.settings import SETTINGS

    r = media
    assert upload(r).status_code == 200 and remove(r).status_code == 200
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
    assert stored(r)[0] == [] and stored(r)[2][0].state == "done"


def test_board_worker_live_protection_lease_fencing_backoff_dead_and_retry(media, monkeypatch):
    r = media
    image = upload(r).json()["media"]
    job = stored(r)[2][0]
    r.client.portal.call(r.cleanup_repository.retry, job.id)
    assert drain(r)["skipped"] == 1 and stored(r)[2][0].state == "protected"
    assert r.client.get(image["url"]).status_code == 200
    assert remove(r).status_code == 200
    first = r.client.portal.call(
        r.cleanup_repository.claim, job.id, r.location.fingerprint, r.location.descriptor
    )
    assert first is not None
    assert not r.client.portal.call(r.cleanup_repository.retry, job.id)
    due(r)
    second = r.client.portal.call(
        r.cleanup_repository.claim, job.id, r.location.fingerprint, r.location.descriptor
    )
    assert second.token != first.token
    assert not r.client.portal.call(r.cleanup_repository.finish, first)
    assert r.client.portal.call(partial(r.cleanup_repository.finish, second, error="unavailable"))
    assert stored(r)[2][0].attempts == 2 and drain(r)["done"] == 0
    original_delete = r.storage.delete
    monkeypatch.setattr(
        r.storage, "delete", AsyncMock(side_effect=StorageError(StorageErrorCode.UNAVAILABLE))
    )
    for attempt in range(3, 6):
        due(r)
        assert drain(r)["failed"] == 1 and stored(r)[2][0].attempts == attempt
    assert stored(r)[2][0].state == "dead"
    r.client.portal.call(r.cleanup_repository.retry, job.id)
    monkeypatch.setattr(r.storage, "delete", original_delete)
    assert drain(r)["done"] == 1


@pytest.mark.parametrize("failure", ["reserve", "replace"])
def test_reservation_or_final_selection_failure_retains_previous_ready_file(
    media, monkeypatch, failure
):
    r = media
    first = upload(r).json()["media"]
    before = revision(r)
    method = "reserve" if failure == "reserve" else "select"
    original = getattr(BoardMediaTransaction, method)

    async def fail(tx, *args, **kwargs):
        await original(tx, *args, **kwargs)
        raise SQLAlchemyError("controlled atomic rollback")

    monkeypatch.setattr(BoardMediaTransaction, method, fail)
    put = AsyncMock(wraps=r.storage.put)
    monkeypatch.setattr(r.storage, "put", put)
    assert upload(r).status_code == 503
    if failure == "reserve":
        put.assert_not_awaited()
    assets, refs, jobs, audits = stored(r)
    assert revision(r) == before and refs[0].asset_id == UUID(first["id"])
    assert next(a for a in assets if a.id == refs[0].asset_id).state == "ready"
    assert r.client.get(first["url"]).status_code == 200
    assert len([a for a in audits if a.action == "media_changed"]) == 1


@pytest.mark.parametrize("field", ["board", "key", "finish"])
def test_corrupt_cleanup_identity_is_blocked_before_candidate_can_be_removed(media, field):
    r = media
    assert upload(r).status_code == 200 and remove(r).status_code == 200
    asset, job = stored(r)[0][0], stored(r)[2][0]
    claim = None
    if field == "finish":
        claim = r.client.portal.call(
            r.cleanup_repository.claim, job.id, r.location.fingerprint, r.location.descriptor
        )

    async def corrupt():
        async with get_db() as db:
            row = await db.get(AssetDeletionOutbox, job.id)
            if field == "board":
                row.board_id = uuid4()
            else:
                row.object_key = f"board-media/{asset.id}/{uuid4().hex}.webp"
            await db.commit()

    r.client.portal.call(corrupt)
    if field == "finish":
        assert not r.client.portal.call(r.cleanup_repository.finish, claim)
    else:
        assert drain(r)["skipped"] == 1
    assert stored(r)[0][0].id == asset.id and stored(r)[2][0].state == "blocked"
    assert r.client.portal.call(r.storage.stat, asset.object_key).size > 0


def test_failed_pending_grace_survives_board_deletion_and_late_put(media, monkeypatch):
    r = media
    original_put = r.storage.put
    monkeypatch.setattr(
        r.storage, "put", AsyncMock(side_effect=StorageError(StorageErrorCode.UNAVAILABLE))
    )
    assert upload(r).status_code == 503
    asset, job = stored(r)[0][0], stored(r)[2][0]
    assert asset.state == "deleting" and job.reason == "upload_failed"

    async def archive():
        async with get_db() as db:
            (await db.get(Board, r.board_id)).status = "archived"
            await db.commit()

    expected = revision(r)
    r.client.portal.call(archive)
    assert (
        r.client.request(
            "DELETE",
            r.path,
            headers=r.headers["owner"],
            json={"expected_revision": expected, "confirm_slug": r.board["slug"]},
        ).status_code
        == 204
    )
    retained = stored(r)[2][0]
    assert retained.reason == "board_deleted" and retained.available_at >= job.available_at
    assert (
        r.client.portal.call(
            r.cleanup_repository.claim, job.id, r.location.fingerprint, r.location.descriptor
        )
        is None
    )
    r.client.portal.call(original_put, asset.object_key, b"late", "image/webp")
    assert drain(r)["done"] == 0
    due(r)
    assert drain(r)["done"] == 1
