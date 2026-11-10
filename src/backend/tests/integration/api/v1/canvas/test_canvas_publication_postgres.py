"""Opt-in real PostgreSQL publication migration, state races and coherent policy reads."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.auth_exception import AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.core.object_storage.identity import StorageLocation
from app.core.object_storage.local import LocalObjectStorage
from app.models.asset import (
    Asset,
    AssetDeletionOutbox,
    AssetRepository,
    AssetTransaction,
    CanvasAssetRef,
)
from app.models.board import Board, BoardMember, BoardTransaction
from app.models.canvas import (
    Canvas,
    CanvasContent,
    CanvasDocumentSaveForm,
    CanvasPatchForm,
    CanvasPublicationTag,
    CanvasPublishForm,
    CanvasRepository,
    CanvasTransaction,
    CanvasUnpublishForm,
    utc_now,
)
from app.models.tag import CanvasTag, Tag
from app.models.user import User, Users
from app.services.asset import AssetService
from app.services.board_permission import BoardPermissionService
from app.services.canvas import CanvasService
from app.services.canvas_access import CanvasAccessService
from tests.fixtures.canvas_document_data import canvas_document
from tests.integration.api.v1.canvas.test_canvas_publication import database_state
from tests.integration.api.v1.tag.test_tag_postgres import seed_existing_content, wait_until_blocked
from tests.unit.services.test_canvas_image import encoded_image

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_publication_transactions(test_db, seed, root):
    owner, writer, board, other, canvas, grades = seed
    access = CanvasAccessService(BoardPermissionService())
    service = CanvasService(access, CanvasRepository())
    repository = AssetRepository()
    storage = LocalObjectStorage(root, 8 * 1024 * 1024)
    await storage.initialize()
    location = StorageLocation("e" * 64, {"provider": "local", "root": str(root)})
    assets = AssetService(access, repository, storage, location)

    async def current_form():
        own = await service.get(writer.id, canvas.id)
        return CanvasPublishForm(
            expected_metadata_revision=own.canvas.revision,
            expected_document_revision=own.document_revision,
            expected_publication_revision=own.publication_revision,
        )

    async def publish():
        return await service.publish(writer.id, canvas.id, await current_form())

    async def withdraw():
        form = await current_form()
        return await service.unpublish(
            writer.id,
            canvas.id,
            CanvasUnpublishForm(expected_publication_revision=form.expected_publication_revision),
        )

    async def upload():
        async def chunks():
            yield encoded_image()

        return await assets.upload(writer.id, canvas.id, chunks())

    async def save(*ids):
        form = await current_form()
        return await service.save_document(
            writer.id,
            canvas.id,
            CanvasDocumentSaveForm(
                expected_revision=form.expected_document_revision,
                document=CanvasContent.model_validate(canvas_document(*ids)),
            ),
        )

    async def finish_tasks(*tasks):
        for task in tasks:
            if task is not None and not task.done():
                task.cancel()
        await asyncio.gather(*[task for task in tasks if task is not None], return_exceptions=True)

    original_board = BoardTransaction.locked_board
    original_read = BoardTransaction.read_board
    entered, pids = asyncio.Event(), []

    async def observed_board(tx, board_id):
        pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
        entered.set()
        return await original_board(tx, board_id)

    async def observed_read(tx, board_id, *, locked=False):
        pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
        entered.set()
        return await original_read(tx, board_id, locked=locked)

    try:
        # Existing data is publishable, including migrated tag IDs and source revisions.
        initial = await publish()
        assert initial.publication_revision == 1 and initial.document_revision == 4
        public = await service.get(None, canvas.id)
        assert public.canvas.tags[0].name == "이전 태그"
        assert public.source_metadata_revision == 0 and public.source_document_revision == 4
        async with test_db() as db:
            assert (
                await db.scalar(
                    text("SELECT pg_typeof(document)::text FROM canvas_publications LIMIT 1")
                )
                == "jsonb"
            )
        first, second = await upload(), await upload()
        await service.change(
            writer.id,
            canvas.id,
            CanvasPatchForm(expected_revision=0, title="새 초안 제목", tag_ids=[]),
        )
        await save(first.id)
        assert await service.get(None, canvas.id) == public
        form = await current_form()
        raced = await asyncio.gather(
            *[service.publish(writer.id, canvas.id, form) for _ in range(2)],
            return_exceptions=True,
        )
        assert sum(not isinstance(item, Exception) for item in raced) == 1
        loser = next(item for item in raced if isinstance(item, Exception))
        assert (
            isinstance(loser, CanvasException)
            and loser.code == CanvasErrorCode.PUBLICATION_CONFLICT.code
        )
        assert loser.details == {"current_revision": 2}
        before = await database_state(test_db)
        assert (await publish()).publication_revision == 2
        assert await database_state(test_db) == before

        # Opposite transitions invalidate the old state token, even with unchanged source.
        old = await current_form()
        assert (await withdraw()).publication_revision == 3
        assert (await withdraw()).publication_revision == 3
        with pytest.raises(CanvasException) as stale:
            await service.publish(writer.id, canvas.id, old)
        assert stale.value.code == CanvasErrorCode.PUBLICATION_CONFLICT.code
        assert (await publish()).publication_revision == 4
        with pytest.raises(CanvasException):
            await service.unpublish(
                writer.id, canvas.id, CanvasUnpublishForm(expected_publication_revision=2)
            )
        await service.change(
            writer.id, canvas.id, CanvasPatchForm(expected_revision=1, summary="새 공개 내용")
        )
        opposing = await current_form()
        raced = await asyncio.gather(
            service.publish(writer.id, canvas.id, opposing),
            service.unpublish(
                writer.id, canvas.id, CanvasUnpublishForm(expected_publication_revision=4)
            ),
            return_exceptions=True,
        )
        assert sum(not isinstance(item, Exception) for item in raced) == 1
        loser = next(item for item in raced if isinstance(item, Exception))
        assert (
            isinstance(loser, CanvasException)
            and loser.code == CanvasErrorCode.PUBLICATION_CONFLICT.code
        )
        assert loser.details == {"current_revision": 5}
        await publish()

        # Save and metadata changes serialize with publication; source clocks identify the winner.
        for editing_document in (True, False):
            form = await current_form()
            before_public = await service.get(None, canvas.id)
            edit = (
                service.save_document(
                    writer.id,
                    canvas.id,
                    CanvasDocumentSaveForm(
                        expected_revision=form.expected_document_revision,
                        document=CanvasContent.model_validate(canvas_document(second.id)),
                    ),
                )
                if editing_document
                else service.change(
                    writer.id,
                    canvas.id,
                    CanvasPatchForm(
                        expected_revision=form.expected_metadata_revision,
                        title="게시와 경쟁한 제목",
                    ),
                )
            )
            raced = await asyncio.gather(
                service.publish(writer.id, canvas.id, form), edit, return_exceptions=True
            )
            assert not isinstance(raced[1], Exception), raced
            public_now = await service.get(None, canvas.id)
            assert public_now == before_public
            if isinstance(raced[0], Exception):
                expected = (
                    CanvasErrorCode.DOCUMENT_CONFLICT
                    if editing_document
                    else CanvasErrorCode.CONFLICT
                )
                assert isinstance(raced[0], CanvasException) and raced[0].code == expected.code
            await publish()

        # Real FK/flush and commit failures roll back the whole publication graph.
        original_refs = AssetTransaction.replace_refs

        async def invalid_ref(tx, current, ids, *, scope):
            await original_refs(tx, current, ids, scope=scope)
            tx._db.add(
                CanvasAssetRef(
                    canvas_id=current.id, board_id=current.board_id, asset_id=uuid4(), scope=scope
                )
            )
            await tx._db.flush()

        for operation in ("publish", "unpublish"):
            if operation == "publish":
                await save(first.id)
            for failure in ("flush", "commit"):
                before = await database_state(test_db)
                target = AssetTransaction if failure == "flush" else AsyncSession
                method = "replace_refs" if failure == "flush" else "commit"
                options = (
                    {"new": invalid_ref}
                    if failure == "flush"
                    else {"side_effect": SQLAlchemyError("controlled commit failure")}
                )
                with patch.object(target, method, **options):
                    with pytest.raises(CanvasException) as rejected:
                        await (publish() if operation == "publish" else withdraw())
                assert rejected.value.code == CanvasErrorCode.UNAVAILABLE.code
                assert await database_state(test_db) == before
        await publish()

        # Publish waits for a Board policy transaction and then sees the revoked grade.
        form = await current_form()
        entered, pids = asyncio.Event(), []
        async with test_db() as blocker:
            await blocker.scalar(select(Board).where(Board.id == board.id).with_for_update())
            (await blocker.get(BoardMember, (board.id, writer.id))).grade_id = grades[0].id
            await blocker.flush()
            before = await database_state(test_db)
            with patch.object(BoardTransaction, "locked_board", new=observed_board):
                pending = asyncio.create_task(service.publish(writer.id, canvas.id, form))
                try:
                    await asyncio.wait_for(entered.wait(), 5)
                    await wait_until_blocked(test_db, pending, pids[0])
                    await blocker.commit()
                    with pytest.raises(CanvasException) as denied:
                        await asyncio.wait_for(pending, 5)
                    assert denied.value.code == CanvasErrorCode.FORBIDDEN.code
                finally:
                    await finish_tasks(pending)
            assert await database_state(test_db) == before
        assert (await withdraw()).publication is None  # withdrawal does not require writing grade
        async with test_db() as db:
            (await db.get(BoardMember, (board.id, writer.id))).grade_id = grades[1].id
            await db.commit()
        await save(second.id)
        await publish()

        # Every public read waits on a restricting Board write; none can use old rights.
        entered, pids = asyncio.Event(), []
        async with test_db() as blocker:
            current = await blocker.scalar(
                select(Board).where(Board.id == board.id).with_for_update()
            )
            current.visibility, current.join_policy = "private", "invite"
            await blocker.flush()
            with patch.object(BoardTransaction, "read_board", new=observed_read):
                pending = [
                    asyncio.create_task(service.get(None, canvas.id)),
                    asyncio.create_task(service.document(None, canvas.id)),
                    asyncio.create_task(assets.read(None, canvas.id, second.id)),
                ]
                try:
                    async with asyncio.timeout(5):
                        while len(pids) < 3:
                            await asyncio.sleep(0.01)
                    for task, pid in zip(pending, pids, strict=True):
                        await wait_until_blocked(test_db, task, pid)
                    await blocker.commit()
                    results = await asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True), 5
                    )
                    assert all(
                        isinstance(item, CanvasException)
                        and item.code == CanvasErrorCode.NOT_FOUND.code
                        for item in results
                    )
                finally:
                    await finish_tasks(*pending)
        async with test_db() as db:
            current = await db.get(Board, board.id)
            current.visibility, current.join_policy = "public", "open"
            await db.commit()

        # Conversely, a coherent public read holds its shared lock through the response snapshot.
        started, release = asyncio.Event(), asyncio.Event()
        original_publication = CanvasTransaction.publication

        async def paused_publication(tx, target):
            result = await original_publication(tx, target)
            started.set()
            await release.wait()
            return result

        expected = await service.get(None, canvas.id)
        with patch.object(CanvasTransaction, "publication", new=paused_publication):
            reading = asyncio.create_task(service.get(None, canvas.id))
            writing = None
            try:
                await asyncio.wait_for(started.wait(), 5)

                async def restrict_board():
                    async with test_db() as db:
                        pid = await db.scalar(text("SELECT pg_backend_pid()"))
                        pids.append(pid)
                        current = await db.scalar(
                            select(Board).where(Board.id == board.id).with_for_update()
                        )
                        current.visibility, current.join_policy = "private", "invite"
                        await db.commit()

                pids = []
                writing = asyncio.create_task(restrict_board())
                async with asyncio.timeout(5):
                    while not pids:
                        await asyncio.sleep(0.01)
                await wait_until_blocked(test_db, writing, pids[0])
                release.set()
                assert await asyncio.wait_for(reading, 5) == expected
                await asyncio.wait_for(writing, 5)
            finally:
                release.set()
                await finish_tasks(reading, writing)
        with pytest.raises(CanvasException):
            await service.get(None, canvas.id)
        async with test_db() as db:
            current = await db.get(Board, board.id)
            current.visibility, current.join_policy = "public", "open"
            await db.commit()

        # Cleanup and withdrawal take the same Board -> Asset -> outbox order in both directions.
        for unpublish_first in (True, False):
            old_image = await upload()
            await save(old_image.id)
            await publish()
            await save(second.id)  # old_image is now referenced only by the publication
            async with test_db() as db:
                job = await db.scalar(
                    select(AssetDeletionOutbox).where(AssetDeletionOutbox.asset_id == old_image.id)
                )
                job.available_at = utc_now() - timedelta(seconds=1)
                job_id = job.id
                await db.commit()
            started, release = asyncio.Event(), asyncio.Event()
            if unpublish_first:

                async def pause_refs(tx, current, ids, *, scope, started=started, release=release):
                    await original_refs(tx, current, ids, scope=scope)
                    started.set()
                    await release.wait()

                patcher = patch.object(AssetTransaction, "replace_refs", new=pause_refs)
            else:
                original_context = AssetTransaction.job_context

                async def pause_cleanup(
                    tx,
                    target,
                    *,
                    original_context=original_context,
                    started=started,
                    release=release,
                ):
                    result = await original_context(tx, target)
                    started.set()
                    await release.wait()
                    return result

                patcher = patch.object(AssetTransaction, "job_context", new=pause_cleanup)
            with patcher:
                # Avoid the draft GET's shared lock before the actual state-changing call.
                form = await current_form()

                async def exact_withdraw(*, form=form):
                    return await service.unpublish(
                        writer.id,
                        canvas.id,
                        CanvasUnpublishForm(
                            expected_publication_revision=form.expected_publication_revision
                        ),
                    )

                leading = asyncio.create_task(
                    exact_withdraw()
                    if unpublish_first
                    else repository.claim(job_id, location.fingerprint)
                )
                trailing = None
                try:
                    await asyncio.wait_for(started.wait(), 5)
                    entered, pids = asyncio.Event(), []
                    with patch.object(BoardTransaction, "locked_board", new=observed_board):
                        trailing = asyncio.create_task(
                            repository.claim(job_id, location.fingerprint)
                            if unpublish_first
                            else exact_withdraw()
                        )
                        await asyncio.wait_for(entered.wait(), 5)
                        await wait_until_blocked(test_db, trailing, pids[0])
                        release.set()
                        leading_result, trailing_result = await asyncio.wait_for(
                            asyncio.gather(leading, trailing), 5
                        )
                finally:
                    release.set()
                    await finish_tasks(leading, trailing)
            claim = trailing_result if unpublish_first else leading_result
            # A completed withdrawal schedules a new grace period before a claim is eligible.
            assert claim is None
            async with test_db() as db:
                assert (await db.get(Asset, old_image.id)).expires_at is not None
                assert (await db.get(Asset, second.id)).expires_at is None
                job = await db.get(AssetDeletionOutbox, job_id)
                assert job.state == "pending"
                job.available_at = utc_now() - timedelta(seconds=1)
                await db.commit()
            claim = await repository.claim(job_id, location.fingerprint)
            assert claim is not None
            await storage.delete(claim.object_key)
            assert await repository.finish(claim)
            await publish()
            assert await assets.read(None, canvas.id, second.id)

        # Actual account deletion races publication without a User/Canvas lock inversion.
        form = await current_form()
        results = await asyncio.wait_for(
            asyncio.gather(
                service.publish(writer.id, canvas.id, form),
                Users.delete_account(writer.id, writer.email),
                return_exceptions=True,
            ),
            5,
        )
        assert not isinstance(results[1], Exception), results
        assert not isinstance(results[0], Exception) or isinstance(
            results[0], (CanvasException, AuthException)
        )
        anonymized = await service.get(None, canvas.id)
        assert anonymized.canvas.author_id is None
        assert await assets.read(None, canvas.id, second.id)
        async with test_db() as db:
            assert await db.get(User, writer.id) is None
            assert await db.get(User, owner.id) is not None
            assert await db.get(Board, other.id) is not None
    finally:
        await storage.close()


def test_real_postgres_publication_migration_state_cas_policy_cleanup_and_account_races(
    monkeypatch, tmp_path
):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_publication_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL,
            connect_args={"server_settings": {"search_path": schema, "statement_timeout": "10000"}},
        )
        created = False

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        async def migrate(target):
            async with engine.begin() as connection:

                def apply(sync_connection):
                    config.attributes["connection"] = sync_connection
                    command.upgrade(config, target)

                await connection.run_sync(apply)

        for model in ("board", "canvas", "asset", "tag", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migrate("0028_canvas_tags")
            seed = await seed_existing_content(test_db)
            canvas = seed[4]
            async with test_db() as db:
                (await db.get(Canvas, canvas.id)).visibility = "public"
                item = Tag(name="이전 태그", normalized_name="이전 태그")
                db.add(item)
                await db.flush()
                db.add(CanvasTag(canvas_id=canvas.id, tag_id=item.id))
                await db.commit()
            from tests.integration.api.v1.canvas.test_canvas_publication import PUBLICATION_MODELS

            legacy_models = tuple(
                model
                for model in PUBLICATION_MODELS
                if not model.__tablename__.startswith("canvas_publication")
            )
            before = await database_state(test_db, legacy_models)
            await migrate("head")
            assert await database_state(test_db, legacy_models) == before
            async with test_db() as db:
                assert (
                    await db.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0032_canvas_comments"
                )
                assert (await db.scalars(select(CanvasPublicationTag))).first() is None
            await assert_publication_transactions(test_db, seed, tmp_path / "publication-assets")
        finally:
            try:
                if created:
                    async with admin.begin() as connection:
                        await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
                        assert (
                            await connection.scalar(
                                text("SELECT count(*) FROM pg_namespace WHERE nspname=:schema"),
                                {"schema": schema},
                            )
                            == 0
                        )
            finally:
                await engine.dispose()
                await admin.dispose()

    asyncio.run(run())
