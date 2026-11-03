"""Real HTTP/SQLite document CAS, policy changes and atomic Asset ref lifecycle."""

import asyncio
from datetime import timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.asset import Asset, AssetDeletionOutbox, AssetTransaction, CanvasAssetRef
from app.models.board import ACTIONS, BoardMember
from app.models.canvas import (
    MAX_CANVAS_REVISION,
    CanvasContent,
    CanvasDocument,
    CanvasDocumentSaveForm,
    CanvasRepository,
    utc_now,
)
from app.models.user import User
from app.services.canvas import CanvasService
from tests.fixtures.canvas_document_data import canvas_document
from tests.integration.api.v1.asset.test_canvas_assets import (
    drain,
    due_now,
    images as images,
    references,
    upload,
)
from tests.integration.api.v1.board.test_board_creation import PAYLOAD
from tests.integration.api.v1.board.test_board_member_administration import roster as roster
from tests.integration.api.v1.canvas.test_canvas_drafts import (
    board_write,
    create,
    draft as draft,
    mutate,
    promote,
    snapshot,
)

pytestmark = pytest.mark.primary_data


def save(r, document=None, *, revision=0, actor="member"):
    return r.client.put(
        r.canvas_path + "/document",
        headers=r.headers[actor],
        json={"expected_revision": revision, "document": document or {}},
    )


def persisted(r):
    async def read():
        async with get_db() as db:
            documents = [
                (d.canvas_id, d.revision, d.document, d.updated_at)
                for d in (
                    await db.scalars(select(CanvasDocument).order_by(CanvasDocument.canvas_id))
                ).all()
            ]
            assets = [
                (a.id, a.state, a.expires_at)
                for a in (await db.scalars(select(Asset).order_by(Asset.id))).all()
            ]
            refs = [
                (ref.canvas_id, ref.asset_id, ref.scope)
                for ref in (
                    await db.scalars(
                        select(CanvasAssetRef).order_by(
                            CanvasAssetRef.canvas_id, CanvasAssetRef.asset_id, CanvasAssetRef.scope
                        )
                    )
                ).all()
            ]
            jobs = [
                (
                    j.id,
                    j.asset_id,
                    j.state,
                    j.reason,
                    j.available_at,
                    j.attempts,
                    j.lease_token,
                    j.last_error,
                )
                for j in (
                    await db.scalars(select(AssetDeletionOutbox).order_by(AssetDeletionOutbox.id))
                ).all()
            ]
            return documents, assets, refs, jobs

    return r.client.portal.call(read)


def test_typed_document_roundtrip_independent_revision_and_repeated_save(images):
    r = images
    asset_id = upload(r).json()["id"]
    document = canvas_document(asset_id)
    before = snapshot(r)
    assert r.canvas["capabilities"]["edit_document"]
    result = save(r, document)
    assert result.status_code == 200, result.text
    assert result.json() == {"revision": 1, "view": "draft"}
    assert result.headers["cache-control"] == "private, no-store"
    loaded = r.client.get(r.canvas_path + "/document", headers=r.headers["member"])
    assert loaded.json() == {
        "revision": 1,
        "view": "draft",
        "document": CanvasContent.model_validate(document).model_dump(mode="json"),
    }
    assert snapshot(r)[:2] == before[:2]
    assert r.client.get(r.canvas_path, headers=r.headers["member"]).json()["document_revision"] == 1
    assert save(r, document, revision=1).json()["revision"] == 2
    duplicate = canvas_document(asset_id, asset_id)
    assert save(r, duplicate, revision=2).json()["revision"] == 3
    assert persisted(r)[2] == [(r.canvas_id, UUID(asset_id), "draft")]
    assert mutate(r, title="본문과 독립적인 제목").json()["canvas"]["revision"] == 1
    before = persisted(r)
    stale = save(r, document, revision=1)
    assert stale.status_code == 409
    assert stale.json()["detail"]["error"] == "CANVAS_DOCUMENT_REVISION_CONFLICT"
    assert stale.json()["detail"]["details"] == {"current_revision": 3}
    assert save(r, {"schema_version": 99}, revision=3).status_code == 422
    assert persisted(r) == before


def test_two_connections_have_one_document_cas_winner_and_only_its_refs(images):
    r = images
    asset_ids = [upload(r).json()["id"] for _ in range(2)]
    service = CanvasService(r.access, CanvasRepository())

    async def compete():
        return await asyncio.gather(
            *[
                service.save_document(
                    r.ids["member"],
                    r.canvas_id,
                    CanvasDocumentSaveForm(
                        expected_revision=0,
                        document=CanvasContent.model_validate(canvas_document(asset_id)),
                    ),
                )
                for asset_id in asset_ids
            ],
            return_exceptions=True,
        )

    results = r.client.portal.call(compete)
    winners = [i for i, item in enumerate(results) if not isinstance(item, Exception)]
    assert len(winners) == 1, results
    loser = results[1 - winners[0]]
    assert (
        isinstance(loser, CanvasException) and loser.code == CanvasErrorCode.DOCUMENT_CONFLICT.code
    )
    assert loser.details == {"current_revision": 1}
    winner = UUID(asset_ids[winners[0]])
    state = persisted(r)
    assert state[0][0][1] == 1
    assert state[2] == [(r.canvas_id, winner, "draft")]
    assert [a[0] for a in state[1] if a[2] is None] == [winner]


@pytest.mark.parametrize(
    "revocation",
    ["grade", "shelf_read", "shelf_write", "archived", "trash", "inactive", "left", "banned"],
)
def test_document_save_rechecks_current_policy_and_state(images, revocation):
    r = images
    asset_id = upload(r).json()["id"]
    if revocation == "grade":
        promote(r, grade=0)
    elif revocation in {"shelf_read", "shelf_write"}:
        actions = {action: None for action in ACTIONS}
        actions["read_canvas" if revocation == "shelf_read" else "create_canvas"] = {
            "audience": "members",
            "min_grade_id": r.grades[2]["id"],
            "staff_only": False,
            "staff_bypass": False,
        }
        assert (
            board_write(
                r, "PUT", f"/api/v1/shelves/{r.shelf_id}/policies", actions=actions
            ).status_code
            == 200
        )
    elif revocation == "archived":
        assert board_write(r, "PATCH", r.path, status="archived").status_code == 200
    elif revocation == "trash":
        assert mutate(r, "DELETE").status_code == 204
    else:

        async def revoke():
            async with get_db() as db:
                if revocation == "inactive":
                    (await db.get(User, r.ids["member"])).is_active = False
                else:
                    member = await db.get(BoardMember, (UUID(r.board["id"]), r.ids["member"]))
                    if revocation == "left":
                        await db.delete(member)
                    else:
                        member.status = "banned"
                await db.commit()

        r.client.portal.call(revoke)
    before = persisted(r)
    denied = save(r, canvas_document(asset_id))
    expected = (
        404
        if revocation == "inactive"
        else 404
        if revocation in {"left", "banned"}
        else 409
        if revocation == "trash"
        else 403
    )
    assert denied.status_code == expected, denied.text
    if revocation in {"grade", "shelf_read", "shelf_write", "archived", "trash"}:
        own = r.client.get(r.canvas_path, headers=r.headers["member"])
        assert own.status_code == 200 and not own.json()["capabilities"]["edit_document"]
        assert (
            r.client.get(r.canvas_path + "/document", headers=r.headers["member"]).status_code
            == 200
        )
    assert persisted(r) == before


@pytest.mark.parametrize(
    "target", ["missing", "other_canvas", "other_board", "pending", "deleting"]
)
def test_invalid_image_references_roll_back_document_and_existing_refs(images, target):
    r = images
    original = upload(r).json()["id"]
    assert save(r, canvas_document(original)).status_code == 200
    if target == "missing":
        invalid = str(uuid4())
    else:
        path = r.assets_path
        if target == "other_canvas":
            path = create(r).headers["location"] + "/assets"
        elif target == "other_board":
            board = r.client.post(
                "/api/v1/boards",
                headers=r.headers["owner"],
                json={**PAYLOAD, "slug": "document-foreign"},
            ).json()
            home = r.client.get(
                f"/api/v1/boards/{board['id']}/home", headers=r.headers["owner"]
            ).json()
            shelf = next(s["id"] for s in home["shelves"] if s["is_default"])
            created = r.client.post(
                f"/api/v1/boards/{board['id']}/canvases",
                headers=r.headers["owner"],
                json={"shelf_id": shelf, "title": "외부"},
            )
            path = created.headers["location"] + "/assets"
        invalid = upload(
            r, actor="owner" if target == "other_board" else "member", path=path
        ).json()["id"]
        if target in {"pending", "deleting"}:

            async def change_state():
                async with get_db() as db:
                    (await db.get(Asset, UUID(invalid))).state = target
                    await db.commit()

            r.client.portal.call(change_state)
    before = persisted(r)
    result = save(r, canvas_document(invalid), revision=1)
    assert (
        result.status_code == 422 and result.json()["detail"]["error"] == "ASSET_INVALID_REFERENCE"
    )
    assert persisted(r) == before


def test_image_removal_deduplicates_and_preserves_publication_refs_until_last_scope(images):
    r = images
    first, second = [UUID(upload(r).json()["id"]) for _ in range(2)]
    assert save(r, canvas_document(first, first, second)).status_code == 200
    references(r, [first], scope="publication")
    assert save(r, canvas_document(first), revision=1).status_code == 200
    state = persisted(r)
    assert next(a for a in state[1] if a[0] == second)[2] is not None
    assert next(j for j in state[3] if j[1] == second)[2:4] == ("pending", "unused_upload")
    assert save(r, canvas_document(), revision=2).status_code == 200
    state = persisted(r)
    assert state[2] == [(r.canvas_id, first, "publication")]
    assert next(a for a in state[1] if a[0] == first)[2] is None
    due_now(r)
    assert drain(r)["done"] == 1
    assert r.client.get(f"{r.assets_path}/{first}", headers=r.headers["member"]).status_code == 200
    references(r, [], scope="publication")
    assert persisted(r)[1][0][2] is not None
    due_now(r)
    assert drain(r)["done"] == 1


@pytest.mark.parametrize("failure", ["refs", "flush", "commit"])
def test_save_failure_rolls_back_document_revision_refs_ttl_and_outbox(images, failure):
    r = images
    first, second = [upload(r).json()["id"] for _ in range(2)]
    assert save(r, canvas_document(first)).status_code == 200
    before = persisted(r)
    original_refs, original_flush = AssetTransaction.replace_refs, AsyncSession.flush

    async def fail_refs(tx, canvas, asset_ids, *, scope):
        await original_refs(tx, canvas, asset_ids, scope=scope)
        raise SQLAlchemyError("after refs")

    async def fail_flush(db, *args, **kwargs):
        # Fail only after the new refs and document CAS have reached the database.
        await original_flush(db, *args, **kwargs)
        if any(
            isinstance(row, AssetDeletionOutbox) and row.state == "protected"
            for row in db.identity_map.values()
        ):
            raise SQLAlchemyError("flush failed")

    target, replacement = (
        ("app.models.asset.AssetTransaction.replace_refs", fail_refs)
        if failure == "refs"
        else ("sqlalchemy.ext.asyncio.AsyncSession.flush", fail_flush)
        if failure == "flush"
        else ("sqlalchemy.ext.asyncio.AsyncSession.commit", SQLAlchemyError("commit failed"))
    )
    options = {"side_effect": replacement} if failure == "commit" else {"new": replacement}
    with patch(target, **options):
        result = save(r, canvas_document(second), revision=1)
    assert result.status_code == 503 and result.json()["detail"]["error"] == "CANVAS_UNAVAILABLE"
    assert persisted(r) == before


def test_ambiguous_commit_keeps_durable_document_and_refs_without_compensation(images):
    r = images
    asset_id = upload(r).json()["id"]
    original = AsyncSession.commit

    async def ambiguous(db):
        await original(db)
        raise SQLAlchemyError("commit acknowledgement lost")

    with patch.object(AsyncSession, "commit", new=ambiguous):
        assert save(r, canvas_document(asset_id)).status_code == 503
    loaded = r.client.get(r.canvas_path + "/document", headers=r.headers["member"])
    assert loaded.json()["revision"] == 1
    assert persisted(r)[2] == [(r.canvas_id, UUID(asset_id), "draft")]
    assert (
        r.client.get(f"{r.assets_path}/{asset_id}", headers=r.headers["member"]).status_code == 200
    )
    assert save(r, canvas_document(asset_id)).status_code == 409


def test_document_revision_maximum_and_missing_row_fail_without_partial_refs(images):
    r = images
    asset_id = upload(r).json()["id"]

    async def set_revision(remove=False):
        async with get_db() as db:
            row = await db.get(CanvasDocument, r.canvas_id)
            if remove:
                await db.delete(row)
            else:
                row.revision = MAX_CANVAS_REVISION
            await db.commit()

    r.client.portal.call(set_revision)
    before = persisted(r)
    maximum = save(r, canvas_document(asset_id), revision=MAX_CANVAS_REVISION)
    assert maximum.status_code == 409 and maximum.json()["detail"]["details"] == {
        "current_revision": MAX_CANVAS_REVISION
    }
    assert persisted(r) == before
    r.client.portal.call(set_revision, True)
    before = persisted(r)
    missing = save(r, canvas_document(asset_id))
    assert missing.status_code == 503 and missing.json()["detail"]["error"] == "CANVAS_UNAVAILABLE"
    assert persisted(r) == before


def test_ready_asset_due_time_is_cleanup_reservation_and_save_protects_it(images):
    r = images
    asset_id = upload(r).json()["id"]

    async def expire():
        async with get_db() as db:
            asset = await db.get(Asset, UUID(asset_id))
            asset.expires_at = utc_now() - timedelta(seconds=1)
            job = await db.scalar(
                select(AssetDeletionOutbox).where(AssetDeletionOutbox.asset_id == asset.id)
            )
            job.available_at = asset.expires_at
            await db.commit()

    r.client.portal.call(expire)
    assert save(r, canvas_document(asset_id)).status_code == 200
    state = persisted(r)
    assert state[1][0][2] is None and state[3][0][2] == "protected"
    assert drain(r)["done"] == 0
