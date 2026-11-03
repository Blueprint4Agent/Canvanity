"""Opt-in PostgreSQL document CAS and lock races in a disposable, unique schema."""

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
from app.core.error.asset_exception import AssetErrorCode, AssetException
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
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardMember,
    BoardMemberGrade,
    BoardRepository,
    BoardTransaction,
)
from app.models.canvas import (
    Canvas,
    CanvasContent,
    CanvasCreateForm,
    CanvasDocument,
    CanvasDocumentSaveForm,
    CanvasRepository,
    utc_now,
)
from app.models.user import User
from app.services.asset import AssetService
from app.services.board import BoardService
from app.services.board_permission import BoardPermissionService
from app.services.canvas import CanvasService
from app.services.canvas_access import CanvasAccessService
from tests.fixtures.canvas_document_data import canvas_document
from tests.unit.services.test_canvas_image import encoded_image

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_document_transactions(test_db, root):
    async with test_db() as db:
        owner, writer = [
            User(
                email=f"pg-document-{name}@example.com",
                name=name,
                role="user",
                is_active=True,
                is_verified=True,
            )
            for name in ("owner", "writer")
        ]
        db.add_all([owner, writer])
        await db.commit()
    boards = BoardService(BoardPermissionService(), BoardRepository())
    board = await boards.create(owner.id, BoardCreateForm(name="저장 경쟁", slug="document-cas"))
    foreign = await boards.create(
        owner.id, BoardCreateForm(name="보존할 보드", slug="document-foreign")
    )
    home = await boards.home(owner.id, board_id=board.id)
    shelf = next(s.id for s in home.shelves if s.is_default)
    async with test_db() as db:
        grades = list(
            (
                await db.scalars(
                    select(BoardMemberGrade)
                    .where(BoardMemberGrade.board_id == board.id)
                    .order_by(BoardMemberGrade.rank)
                )
            ).all()
        )
        db.add(
            BoardMember(
                board_id=board.id,
                user_id=writer.id,
                role="member",
                grade_id=grades[1].id,
                status="active",
            )
        )
        await db.commit()
    access, repository = CanvasAccessService(BoardPermissionService()), AssetRepository()
    service = CanvasService(access, CanvasRepository())
    canvas = (
        await service.create(
            writer.id, board.id, CanvasCreateForm(shelf_id=shelf, title="한글 본문")
        )
    ).canvas
    storage = LocalObjectStorage(root, 8 * 1024 * 1024)
    await storage.initialize()
    location = StorageLocation("b" * 64, {"provider": "local", "root": str(root)})
    assets = AssetService(access, repository, storage, location)

    async def upload():
        async def chunks():
            yield encoded_image()

        return await assets.upload(writer.id, canvas.id, chunks())

    async def save(revision, *ids):
        return await service.save_document(
            writer.id,
            canvas.id,
            CanvasDocumentSaveForm(
                expected_revision=revision,
                document=CanvasContent.model_validate(canvas_document(*ids)),
            ),
        )

    async def state():
        async with test_db() as db:
            result = []
            for model in (Canvas, CanvasDocument, Asset, CanvasAssetRef, AssetDeletionOutbox):
                rows = (
                    await db.scalars(select(model).order_by(*model.__table__.primary_key.columns))
                ).all()
                result.append(
                    [
                        tuple(getattr(row, column.name) for column in model.__table__.columns)
                        for row in rows
                    ]
                )
            return result

    async def blocked(task, pid):
        async with asyncio.timeout(5):
            while True:
                async with test_db() as db:
                    waiting = await db.scalar(
                        text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": pid}
                    )
                if waiting:
                    return
                assert not task.done(), "The competing transaction did not wait for the lock"
                await asyncio.sleep(0.01)

    async def current_revision():
        return (await service.document(writer.id, canvas.id)).revision

    try:
        first, second = await upload(), await upload()
        initial = await service.get(writer.id, canvas.id)
        assert (await save(0, first.id)).revision == 1
        loaded = await service.document(writer.id, canvas.id)
        assert loaded.document == CanvasContent.model_validate(canvas_document(first.id))
        assert loaded.document.nodes[0].engine_element.text.startswith("한글 캔버스")
        assert (await service.get(writer.id, canvas.id)).canvas == initial.canvas
        async with test_db() as db:
            assert (
                await db.scalar(
                    text(
                        "SELECT pg_typeof(document)::text FROM canvas_documents WHERE canvas_id=:id"
                    ),
                    {"id": canvas.id},
                )
                == "jsonb"
            )
        raced = await asyncio.gather(save(1, first.id), save(1, second.id), return_exceptions=True)
        assert sum(not isinstance(item, Exception) for item in raced) == 1, raced
        loser = next(item for item in raced if isinstance(item, Exception))
        assert (
            isinstance(loser, CanvasException)
            and loser.code == CanvasErrorCode.DOCUMENT_CONFLICT.code
        )
        assert loser.details == {"current_revision": 2}
        winner = first.id if not isinstance(raced[0], Exception) else second.id
        async with test_db() as db:
            assert list(
                (
                    await db.scalars(
                        select(CanvasAssetRef.asset_id).where(CanvasAssetRef.canvas_id == canvas.id)
                    )
                ).all()
            ) == [winner]

        # Real FK/flush and commit failures happen after CAS and ref replacement.
        original_refs = AssetTransaction.replace_refs

        async def invalid_ref(tx, current, asset_ids, *, scope):
            await original_refs(tx, current, asset_ids, scope=scope)
            tx._db.add(
                CanvasAssetRef(
                    board_id=current.board_id, canvas_id=current.id, asset_id=uuid4(), scope="draft"
                )
            )
            await tx._db.flush()

        for failure in ("flush", "commit"):
            before = await state()
            target = (
                "app.models.asset.AssetTransaction.replace_refs"
                if failure == "flush"
                else "sqlalchemy.ext.asyncio.AsyncSession.commit"
            )
            options = (
                {"new": invalid_ref}
                if failure == "flush"
                else {"side_effect": SQLAlchemyError("commit failed")}
            )
            with patch(target, **options):
                with pytest.raises(CanvasException) as rejected:
                    await save(2, first.id, second.id)
            assert rejected.value.code == CanvasErrorCode.UNAVAILABLE.code
            assert await state() == before
        before = await state()
        with pytest.raises(AssetException) as invalid:
            await save(2, uuid4())
        assert invalid.value.code == AssetErrorCode.INVALID_REFERENCE.code
        assert await state() == before

        # A policy transaction commits while save waits on the same Board lock.
        entered, pids = asyncio.Event(), []
        original_board = BoardTransaction.locked_board

        async def observed_board(tx, board_id):
            pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
            entered.set()
            return await original_board(tx, board_id)

        async with test_db() as blocker:
            await blocker.scalar(select(Board).where(Board.id == board.id).with_for_update())
            member = await blocker.get(BoardMember, (board.id, writer.id))
            member.grade_id = grades[0].id
            await blocker.flush()
            before = await state()
            with patch.object(BoardTransaction, "locked_board", new=observed_board):
                pending = asyncio.create_task(save(2, first.id))
                try:
                    await asyncio.wait_for(entered.wait(), 5)
                    await blocked(pending, pids[0])
                    await blocker.commit()
                    with pytest.raises(CanvasException) as denied:
                        await asyncio.wait_for(pending, 5)
                    assert denied.value.code == CanvasErrorCode.FORBIDDEN.code
                finally:
                    if not pending.done():
                        pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)
            assert await state() == before
        own = await service.get(writer.id, canvas.id)
        assert own.capabilities.read_document and not own.capabilities.edit_document
        async with test_db() as db:
            (await db.get(BoardMember, (board.id, writer.id))).grade_id = grades[1].id
            await db.commit()

        # Force both orderings: save owns the lock first, then cleanup owns it first.
        for save_first in (True, False):
            image = await upload()
            async with test_db() as db:
                asset = await db.get(Asset, image.id)
                asset.expires_at = utc_now() - timedelta(seconds=1)
                job = await db.scalar(
                    select(AssetDeletionOutbox).where(AssetDeletionOutbox.asset_id == image.id)
                )
                job.available_at = asset.expires_at
                job_id = job.id
                await db.commit()
            revision = await current_revision()
            started, release = asyncio.Event(), asyncio.Event()
            if save_first:

                async def pause_refs(
                    tx, current, asset_ids, *, scope, started=started, release=release
                ):
                    await original_refs(tx, current, asset_ids, scope=scope)
                    started.set()
                    await release.wait()

                with patch.object(AssetTransaction, "replace_refs", new=pause_refs):
                    saving = asyncio.create_task(save(revision, image.id))
                    claiming = None
                    try:
                        await asyncio.wait_for(started.wait(), 5)
                        entered, pids = asyncio.Event(), []
                        with patch.object(BoardTransaction, "locked_board", new=observed_board):
                            claiming = asyncio.create_task(
                                repository.claim(job_id, location.fingerprint)
                            )
                            await asyncio.wait_for(entered.wait(), 5)
                            await blocked(claiming, pids[0])
                            release.set()
                            assert (await asyncio.wait_for(saving, 5)).revision == revision + 1
                            assert await asyncio.wait_for(claiming, 5) is None
                    finally:
                        release.set()
                        for task in (saving, claiming):
                            if task is not None and not task.done():
                                task.cancel()
                        await asyncio.gather(
                            *[task for task in (saving, claiming) if task is not None],
                            return_exceptions=True,
                        )
                async with test_db() as db:
                    assert (await db.get(Asset, image.id)).expires_at is None
                    assert (await db.get(AssetDeletionOutbox, job_id)).state == "protected"
            else:
                original_context = AssetTransaction.job_context

                async def pause_claim(
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

                before = await service.document(writer.id, canvas.id)
                with patch.object(AssetTransaction, "job_context", new=pause_claim):
                    claiming = asyncio.create_task(repository.claim(job_id, location.fingerprint))
                    saving = None
                    try:
                        await asyncio.wait_for(started.wait(), 5)
                        entered, pids = asyncio.Event(), []
                        with patch.object(BoardTransaction, "locked_board", new=observed_board):
                            saving = asyncio.create_task(save(revision, image.id))
                            await asyncio.wait_for(entered.wait(), 5)
                            await blocked(saving, pids[0])
                            release.set()
                            claim = await asyncio.wait_for(claiming, 5)
                            assert claim is not None
                            with pytest.raises(AssetException) as denied:
                                await asyncio.wait_for(saving, 5)
                            assert denied.value.code == AssetErrorCode.INVALID_REFERENCE.code
                    finally:
                        release.set()
                        for task in (saving, claiming):
                            if task is not None and not task.done():
                                task.cancel()
                        await asyncio.gather(
                            *[task for task in (saving, claiming) if task is not None],
                            return_exceptions=True,
                        )
                assert await service.document(writer.id, canvas.id) == before
                async with test_db() as db:
                    assert (
                        await db.scalar(
                            select(CanvasAssetRef.asset_id).where(
                                CanvasAssetRef.asset_id == image.id
                            )
                        )
                        is None
                    )
                await storage.delete(claim.object_key)
                assert await repository.finish(claim)
        async with test_db() as db:
            assert (await db.get(Board, foreign.id)).name == "보존할 보드"
            assert (await db.get(User, owner.id)).is_active
    finally:
        await storage.close()


def test_real_postgres_document_cas_rollback_permission_and_cleanup_races(monkeypatch, tmp_path):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_document_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL, connect_args={"server_settings": {"search_path": schema}}
        )
        created = False

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        for model in ("board", "canvas", "asset", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            async with engine.begin() as connection:

                def migrate(sync_connection):
                    config.attributes["connection"] = sync_connection
                    command.upgrade(config, "head")

                await connection.run_sync(migrate)
            await assert_document_transactions(test_db, tmp_path / "pg-document-assets")
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
