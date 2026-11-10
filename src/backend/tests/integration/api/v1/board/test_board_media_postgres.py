"""Opt-in isolated PostgreSQL migration preservation, locks, races and real private files."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.board_exception import BoardErrorCode, BoardException
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
    BoardDeleteForm,
    BoardMember,
    BoardMemberAudit,
    BoardRepository,
    BoardTransaction,
)
from app.models.board_media import (
    BoardMediaAsset,
    BoardMediaChangeForm,
    BoardMediaRef,
    BoardMediaRepository,
    BoardMediaTransaction,
    now,
)
from app.models.user import User
from app.services.asset_cleanup import AssetCleanupService
from app.services.board import BoardService
from app.services.board_media import BoardMediaService
from app.services.board_permission import BoardPermissionService
from tests.integration.api.v1.canvas.test_canvas_feed import seed_feed
from tests.integration.api.v1.tag.test_tag_postgres import wait_until_blocked
from tests.unit.services.test_canvas_image import encoded_image

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def old_state(test_db):
    async with test_db() as db:
        connection = await db.connection()
        names = [
            name
            for name in await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            if name not in {"alembic_version", "board_media_assets", "board_media_refs"}
        ]
        return {
            name: sorted(
                [tuple(row) for row in (await db.execute(text(f'SELECT * FROM "{name}"'))).all()],
                key=repr,
            )
            for name in names
        }


async def seed_legacy(test_db):
    r = await seed_feed(test_db)
    async with test_db() as db:
        asset_id = uuid4()
        key = f"canvas-assets/{asset_id}/{uuid4().hex}.webp"
        location = {"provider": "local", "root": "/isolated-legacy-media"}
        db.add(
            Asset(
                id=asset_id,
                board_id=r.boards[0].id,
                canvas_id=r.canvases[0].id,
                owner_id=r.writer.id,
                object_key=key,
                storage_fingerprint="a" * 64,
                storage_location=location,
                byte_size=2,
                width=1,
                height=1,
                frame_count=1,
                sha256="b" * 64,
                state="ready",
                upload_deadline=now(),
            )
        )
        await db.flush()
        db.add_all(
            [
                CanvasAssetRef(
                    board_id=r.boards[0].id,
                    canvas_id=r.canvases[0].id,
                    asset_id=asset_id,
                    scope=scope,
                )
                for scope in ("draft", "publication")
            ]
        )
        db.add(
            AssetDeletionOutbox(
                asset_id=asset_id,
                board_id=r.boards[0].id,
                object_key=key,
                storage_fingerprint="a" * 64,
                storage_location=location,
                reason="preserved",
                state="processing",
                attempts=3,
                lease_token=uuid4(),
                last_error="unavailable",
                available_at=now() + timedelta(days=1),
            )
        )
        (await db.get(User, r.reader.id)).profile_photo = {
            "key": "profile-photos/preserved.webp",
            "storage": "legacy",
        }
        await db.commit()
    return r


async def exercise(test_db, r, storage, location):
    repository = BoardMediaRepository()
    service = BoardMediaService(BoardPermissionService(), repository, storage, location)
    boards = BoardService(BoardPermissionService(), BoardRepository())
    cleanup_repository = AssetRepository()
    cleanup = AssetCleanupService(cleanup_repository, storage, location)
    ident = r.boards[0].id

    async def revision():
        async with test_db() as db:
            return (await db.get(Board, ident)).revision

    async def upload(*, user_id=None, expected=None, slot="cover"):
        async def chunks():
            yield encoded_image()

        return await service.upload(
            user_id or r.owner.id,
            ident,
            slot,
            BoardMediaChangeForm(
                expected_revision=await revision() if expected is None else expected,
                reason="실제 PG 검증",
            ),
            chunks(),
        )

    async def rows():
        async with test_db() as db:
            return (
                list(
                    (
                        await db.scalars(
                            select(BoardMediaAsset).where(BoardMediaAsset.board_id == ident)
                        )
                    ).all()
                ),
                list(
                    (
                        await db.scalars(
                            select(BoardMediaRef).where(BoardMediaRef.board_id == ident)
                        )
                    ).all()
                ),
                list(
                    (
                        await db.scalars(
                            select(BoardMemberAudit).where(
                                BoardMemberAudit.board_id == ident,
                                BoardMemberAudit.action == "media_changed",
                            )
                        )
                    ).all()
                ),
            )

    # Two independent reserved puts reach finalization with the same Board clock.
    original_put = storage.put
    entered, release, count = asyncio.Event(), asyncio.Event(), 0

    async def racing_put(key, data, content_type):
        nonlocal count
        await original_put(key, data, content_type)
        count += 1
        if count == 2:
            entered.set()
        await release.wait()

    expected = await revision()
    with patch.object(storage, "put", racing_put):
        tasks = [asyncio.create_task(upload(expected=expected)) for _ in range(2)]
        try:
            await asyncio.wait_for(entered.wait(), 5)
            async with test_db() as db:
                assert (await db.get(Board, ident)).revision == expected
                assert (
                    await db.scalar(
                        select(BoardMediaRef.asset_id).where(BoardMediaRef.board_id == ident)
                    )
                    is None
                )
            release.set()
            result = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            release.set()
            await asyncio.gather(*tasks, return_exceptions=True)
    assert sum(not isinstance(item, Exception) for item in result) == 1, result
    loser = next(item for item in result if isinstance(item, Exception))
    assert isinstance(loser, BoardException) and loser.code == BoardErrorCode.CONFLICT.code
    winner = next(item for item in result if not isinstance(item, Exception))
    assert len((await rows())[2]) == 1 and await revision() == expected + 1
    assert len(await service.read(None, ident, "cover", winner.media.id)) == winner.media.byte_size

    # A waiting finalizer reads the role/state revoked under the shared Board lock.
    async with test_db() as db:
        (await db.get(BoardMember, (ident, r.writer.id))).role = "admin"
        await db.commit()
    for revoke in ("role", "board"):
        put_entered, put_release, lock_entered = asyncio.Event(), asyncio.Event(), asyncio.Event()
        pids = []

        async def paused_put(
            key, data, content_type, put_entered=put_entered, put_release=put_release
        ):
            await original_put(key, data, content_type)
            put_entered.set()
            await put_release.wait()

        original_lock = BoardTransaction.locked_board

        async def observed_lock(
            tx, board_id, lock_entered=lock_entered, original_lock=original_lock, pids=pids
        ):
            pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
            lock_entered.set()
            return await original_lock(tx, board_id)

        with patch.object(storage, "put", paused_put):
            task = asyncio.create_task(upload(user_id=r.writer.id))
            try:
                await asyncio.wait_for(put_entered.wait(), 5)
                async with test_db() as blocker:
                    board = await blocker.scalar(
                        select(Board).where(Board.id == ident).with_for_update()
                    )
                    if revoke == "role":
                        (await blocker.get(BoardMember, (ident, r.writer.id))).role = "member"
                    else:
                        board.status = "archived"
                    await blocker.flush()
                    with patch.object(BoardTransaction, "locked_board", observed_lock):
                        put_release.set()
                        await asyncio.wait_for(lock_entered.wait(), 5)
                        await wait_until_blocked(test_db, task, pids[-1])
                        await blocker.commit()
                        with pytest.raises(BoardException) as caught:
                            await asyncio.wait_for(task, 5)
                        assert caught.value.code == BoardErrorCode.FORBIDDEN.code
            finally:
                put_release.set()
                await asyncio.gather(task, return_exceptions=True)
        async with test_db() as db:
            (await db.get(Board, ident)).status = "active"
            (await db.get(BoardMember, (ident, r.writer.id))).role = "admin"
            await db.commit()
    assert len((await rows())[2]) == 1

    # The User SHARE lock waits for a concurrent deactivation before authorization.
    entered, pids = asyncio.Event(), []
    original_user_lock = BoardTransaction.lock_active_user

    async def observed_user(tx, user_id):
        pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
        entered.set()
        return await original_user_lock(tx, user_id)

    async with test_db() as blocker:
        user = await blocker.scalar(select(User).where(User.id == r.writer.id).with_for_update())
        user.is_active = False
        await blocker.flush()
        with patch.object(BoardTransaction, "lock_active_user", observed_user):
            task = asyncio.create_task(upload(user_id=r.writer.id))
            try:
                await asyncio.wait_for(entered.wait(), 5)
                await wait_until_blocked(test_db, task, pids[-1])
                await blocker.commit()
                with pytest.raises(BoardException) as caught:
                    await asyncio.wait_for(task, 5)
                assert caught.value.code == BoardErrorCode.NOT_FOUND.code
            finally:
                await asyncio.gather(task, return_exceptions=True)
    async with test_db() as db:
        (await db.get(User, r.writer.id)).is_active = True
        await db.commit()

    # Current FK rejects cross Board/slot/non-ready references and deleting a selected target.
    current = (await rows())[1][0]
    for kind in ("state", "slot", "board", "pending"):
        async with test_db() as db:
            if kind == "state":
                (await db.get(BoardMediaAsset, current.asset_id)).state = "deleting"
            else:
                db.add(
                    BoardMediaRef(
                        board_id=r.boards[1].id if kind == "board" else ident,
                        slot="avatar",
                        asset_id=current.asset_id,
                        asset_state="pending" if kind == "pending" else "ready",
                    )
                )
            with pytest.raises(SQLAlchemyError):
                await db.commit()

    # List/Home media hydration observes the same RR snapshot as Board/role/clock.
    before = await boards.list(None, limit=100, cursor=None, q="", interest_id=None, mine=False)
    original_batch = BoardTransaction.media_batch
    entered, release = asyncio.Event(), asyncio.Event()

    async def paused_batch(tx, board_ids):
        assert await tx._db.scalar(text("SHOW transaction_isolation")) == "repeatable read"
        assert await tx._db.scalar(text("SHOW transaction_read_only")) == "on"
        entered.set()
        await release.wait()
        return await original_batch(tx, board_ids)

    with patch.object(BoardTransaction, "media_batch", paused_batch):
        task = asyncio.create_task(
            boards.list(None, limit=100, cursor=None, q="", interest_id=None, mine=False)
        )
        try:
            await asyncio.wait_for(entered.wait(), 5)
            replacement = await upload()
            release.set()
            assert await asyncio.wait_for(task, 5) == before
        finally:
            release.set()
            await asyncio.gather(task, return_exceptions=True)
    with pytest.raises(BoardException):
        await service.read(None, ident, "cover", winner.media.id)
    assert (await boards.home(None, board_id=ident)).board.cover.id == replacement.media.id

    # Rollback preserves the selected file and clock; deletion commits parentless intent.
    stable = await rows()
    original_select = BoardMediaTransaction.select

    async def failed_select(tx, *args, **kwargs):
        await original_select(tx, *args, **kwargs)
        raise SQLAlchemyError("controlled selection flush rollback")

    with (
        patch.object(BoardMediaTransaction, "select", failed_select),
        pytest.raises(BoardException),
    ):
        await service.remove(
            r.owner.id,
            ident,
            "cover",
            BoardMediaChangeForm(expected_revision=await revision(), reason="롤백"),
        )
    assert [(a.id, a.state) for a in (await rows())[0]] == [(a.id, a.state) for a in stable[0]]
    async with test_db() as db:
        (await db.get(Board, ident)).status = "archived"
        await db.commit()
    # Drain selected/failed/orphan entries after Board deletion, retaining other Board and legacy files.
    await boards.delete_board(
        r.owner.id,
        ident,
        BoardDeleteForm(expected_revision=await revision(), confirm_slug=r.boards[0].slug),
    )
    async with test_db() as db:
        assert await db.get(Board, ident) is None
        assert await db.get(Board, r.boards[1].id) is not None
        for job in (
            await db.scalars(
                select(AssetDeletionOutbox).where(
                    AssetDeletionOutbox.object_key.startswith("board-media/")
                )
            )
        ).all():
            job.available_at = now() - timedelta(seconds=1)
        await db.commit()
    result = await cleanup.drain(limit=100)
    assert result["done"] >= 4
    async with test_db() as db:
        assert not (
            await db.scalars(select(BoardMediaAsset).where(BoardMediaAsset.board_id == ident))
        ).all()


async def cleanup_delete_races(test_db, r, storage, location):
    repository = AssetRepository()
    media = BoardMediaService(BoardPermissionService(), BoardMediaRepository(), storage, location)
    boards = BoardService(BoardPermissionService(), BoardRepository())
    cleanup = AssetCleanupService(repository, storage, location)
    for index, board_summary in enumerate(r.boards[1:3]):
        ident = board_summary.id

        async def upload(expected, ident=ident):
            async def chunks():
                yield encoded_image()

            return await media.upload(
                r.owner.id,
                ident,
                "cover",
                BoardMediaChangeForm(expected_revision=expected, reason="삭제 경쟁"),
                chunks(),
            )

        first = await upload(0)
        await upload(1)
        async with test_db() as db:
            board = await db.get(Board, ident)
            board.status = "archived"
            await db.commit()
            job = await db.scalar(
                select(AssetDeletionOutbox).where(AssetDeletionOutbox.asset_id == first.media.id)
            )
            job_id, key = job.id, job.object_key
        entered, release, pids = asyncio.Event(), asyncio.Event(), []
        original_lock = BoardTransaction.locked_board

        async def observed_lock(
            tx, board_id, entered=entered, original_lock=original_lock, pids=pids
        ):
            pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
            entered.set()
            return await original_lock(tx, board_id)

        if index == 0:
            # Board deletion commits while a real cleanup claim waits on the Board lock.
            async with test_db() as blocker:
                board = await blocker.scalar(
                    select(Board).where(Board.id == ident).with_for_update()
                )
                with patch.object(BoardTransaction, "locked_board", observed_lock):
                    task = asyncio.create_task(
                        repository.claim(job_id, location.fingerprint, location.descriptor)
                    )
                    await asyncio.wait_for(entered.wait(), 5)
                    await wait_until_blocked(test_db, task, pids[-1])
                    await BoardTransaction(blocker).delete_board(board)
                    await blocker.commit()
                    claim = await asyncio.wait_for(task, 5)
            assert claim is not None
            await storage.delete(key)
            assert await repository.finish(claim)
        else:
            # Cleanup owns Board/Asset/outbox first. Deletion waits, then re-enqueues and fences the lease.
            original_context = AssetTransaction.job_context

            async def paused_context(
                tx,
                requested,
                entered=entered,
                job_id=job_id,
                original_context=original_context,
                release=release,
            ):
                result = await original_context(tx, requested)
                if requested == job_id:
                    entered.set()
                    await release.wait()
                return result

            with patch.object(AssetTransaction, "job_context", paused_context):
                claim_task = asyncio.create_task(
                    repository.claim(job_id, location.fingerprint, location.descriptor)
                )
                await asyncio.wait_for(entered.wait(), 5)
                entered.clear()
                try:
                    with patch.object(BoardTransaction, "locked_board", observed_lock):
                        delete_task = asyncio.create_task(
                            boards.delete_board(
                                r.owner.id,
                                ident,
                                BoardDeleteForm(
                                    expected_revision=2, confirm_slug=board_summary.slug
                                ),
                            )
                        )
                        await asyncio.wait_for(entered.wait(), 5)
                        await wait_until_blocked(test_db, delete_task, pids[-1])
                        release.set()
                        claim = await asyncio.wait_for(claim_task, 5)
                        await asyncio.wait_for(delete_task, 5)
                finally:
                    release.set()
                    await asyncio.gather(claim_task, return_exceptions=True)
            assert claim is not None
            await storage.delete(key)
            assert not await repository.finish(claim)
        assert (await cleanup.drain(limit=100))["done"] >= 1
        async with test_db() as db:
            assert await db.get(Board, ident) is None
            assert await db.get(Board, r.boards[3].id) is not None

    # A put completing after Board deletion and a done tombstone reopens durable cleanup.
    late = await boards.create(
        r.owner.id, BoardCreateForm(name="늦은 업로드", slug="late-board-put")
    )
    entered, release = asyncio.Event(), asyncio.Event()
    original_put = storage.put

    async def paused_put(key, data, content_type):
        entered.set()
        await release.wait()
        return await original_put(key, data, content_type)

    async def chunks():
        yield encoded_image()

    with patch.object(storage, "put", paused_put):
        task = asyncio.create_task(
            media.upload(
                r.owner.id,
                late.id,
                "cover",
                BoardMediaChangeForm(expected_revision=0, reason="늦은 업로드"),
                chunks(),
            )
        )
        try:
            await asyncio.wait_for(entered.wait(), 5)
            await boards.delete_board(
                r.owner.id, late.id, BoardDeleteForm(expected_revision=0, confirm_slug=late.slug)
            )
            async with test_db() as db:
                job = await db.scalar(
                    select(AssetDeletionOutbox).where(AssetDeletionOutbox.board_id == late.id)
                )
                job.available_at = now() - timedelta(seconds=1)
                job_id, key = job.id, job.object_key
                await db.commit()
            assert (await cleanup.drain(limit=100))["done"] == 1
            release.set()
            with pytest.raises(BoardException):
                await asyncio.wait_for(task, 5)
        finally:
            release.set()
            await asyncio.gather(task, return_exceptions=True)
    assert (await storage.stat(key)).size > 0
    async with test_db() as db:
        job = await db.get(AssetDeletionOutbox, job_id)
        assert job.state == "pending" and job.reason == "upload_failed"
        job.available_at = now() - timedelta(seconds=1)
        await db.commit()
    assert (await cleanup.drain(limit=100))["done"] == 1


async def upload_delete_races(test_db, r, storage, location):
    repository = BoardMediaRepository()
    cleanup_repository = AssetRepository()
    cleanup = AssetCleanupService(cleanup_repository, storage, location)
    service = BoardMediaService(BoardPermissionService(), repository, storage, location)
    boards = BoardService(BoardPermissionService(), BoardRepository())
    original_put = storage.put
    for mode in ("deletion-first", "finalize-first", "expired-claim"):
        board = await boards.create(r.owner.id, BoardCreateForm(name="업로드 삭제 경쟁", slug=mode))
        put_entered, put_release, tx_entered, tx_release, lock_entered = [
            asyncio.Event() for _ in range(5)
        ]
        pids = []

        async def paused_put(
            key, data, content_type, put_entered=put_entered, put_release=put_release
        ):
            put_entered.set()
            await put_release.wait()
            return await original_put(key, data, content_type)

        async def chunks():
            yield encoded_image()

        original_lock = BoardTransaction.locked_board

        async def observed_lock(
            tx, ident, lock_entered=lock_entered, original_lock=original_lock, pids=pids
        ):
            pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
            lock_entered.set()
            return await original_lock(tx, ident)

        with patch.object(storage, "put", paused_put):
            upload_task = asyncio.create_task(
                service.upload(
                    r.owner.id,
                    board.id,
                    "cover",
                    BoardMediaChangeForm(expected_revision=0, reason="업로드 경쟁"),
                    chunks(),
                )
            )
            delete_task = None
            try:
                await asyncio.wait_for(put_entered.wait(), 5)
                async with test_db() as db:
                    job = await db.scalar(
                        select(AssetDeletionOutbox).where(AssetDeletionOutbox.board_id == board.id)
                    )
                    job_id = job.id
                if mode == "deletion-first":
                    original_delete = BoardTransaction.delete_board

                    async def paused_delete(
                        tx,
                        selected,
                        original_delete=original_delete,
                        tx_entered=tx_entered,
                        tx_release=tx_release,
                    ):
                        tx_entered.set()
                        await tx_release.wait()
                        return await original_delete(tx, selected)

                    with patch.object(BoardTransaction, "delete_board", paused_delete):
                        delete_task = asyncio.create_task(
                            boards.delete_board(
                                r.owner.id,
                                board.id,
                                BoardDeleteForm(expected_revision=0, confirm_slug=board.slug),
                            )
                        )
                        await asyncio.wait_for(tx_entered.wait(), 5)
                        with patch.object(BoardTransaction, "locked_board", observed_lock):
                            put_release.set()
                            await asyncio.wait_for(lock_entered.wait(), 5)
                            await wait_until_blocked(test_db, upload_task, pids[-1])
                            tx_release.set()
                            await asyncio.wait_for(delete_task, 5)
                            with pytest.raises(BoardException) as caught:
                                await asyncio.wait_for(upload_task, 5)
                            assert caught.value.code == BoardErrorCode.NOT_FOUND.code
                elif mode == "finalize-first":
                    original_select = BoardMediaTransaction.select

                    async def paused_select(
                        tx,
                        *args,
                        original_select=original_select,
                        tx_entered=tx_entered,
                        tx_release=tx_release,
                        **kwargs,
                    ):
                        tx_entered.set()
                        await tx_release.wait()
                        return await original_select(tx, *args, **kwargs)

                    with patch.object(BoardMediaTransaction, "select", paused_select):
                        put_release.set()
                        await asyncio.wait_for(tx_entered.wait(), 5)
                        with patch.object(BoardTransaction, "locked_board", observed_lock):
                            delete_task = asyncio.create_task(
                                boards.delete_board(
                                    r.owner.id,
                                    board.id,
                                    BoardDeleteForm(expected_revision=0, confirm_slug=board.slug),
                                )
                            )
                            await asyncio.wait_for(lock_entered.wait(), 5)
                            await wait_until_blocked(test_db, delete_task, pids[-1])
                            tx_release.set()
                            result = await asyncio.wait_for(upload_task, 5)
                            assert result.board_revision == 1
                            with pytest.raises(BoardException) as caught:
                                await asyncio.wait_for(delete_task, 5)
                            assert caught.value.code == BoardErrorCode.CONFLICT.code
                    assert await service.read(None, board.id, "cover", result.media.id)
                    # A deliberate retry uses the new revision and records the selected file intent.
                    await boards.delete_board(
                        r.owner.id,
                        board.id,
                        BoardDeleteForm(expected_revision=1, confirm_slug=board.slug),
                    )
                else:
                    async with test_db() as db:
                        asset = await db.scalar(
                            select(BoardMediaAsset).where(BoardMediaAsset.board_id == board.id)
                        )
                        asset.upload_deadline = now() - timedelta(seconds=1)
                        (
                            await db.get(AssetDeletionOutbox, job_id)
                        ).available_at = asset.upload_deadline
                        await db.commit()
                    assert (await cleanup.drain(limit=100))["done"] == 1
                    put_release.set()
                    with pytest.raises(BoardException) as caught:
                        await asyncio.wait_for(upload_task, 5)
                    assert caught.value.code == BoardErrorCode.MEDIA_CONFLICT.code
                    async with test_db() as db:
                        assert (await db.get(AssetDeletionOutbox, job_id)).state == "pending"
                    await boards.delete_board(
                        r.owner.id,
                        board.id,
                        BoardDeleteForm(expected_revision=0, confirm_slug=board.slug),
                    )
            finally:
                put_release.set()
                tx_release.set()
                await asyncio.gather(
                    upload_task, *([delete_task] if delete_task else []), return_exceptions=True
                )
        async with test_db() as db:
            job = await db.get(AssetDeletionOutbox, job_id)
            assert job is not None and job.state == "pending"
            job.available_at = now() - timedelta(seconds=1)
            await db.commit()
        assert (await cleanup.drain(limit=100))["done"] == 1


def test_real_postgres_board_media_migration_locks_cas_snapshot_and_files(monkeypatch, tmp_path):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_media_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL,
            connect_args={"server_settings": {"search_path": schema, "statement_timeout": "10000"}},
        )

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        async def migrate(target, downgrade=False):
            async with engine.begin() as connection:

                def apply(sync):
                    config.attributes["connection"] = sync
                    (command.downgrade if downgrade else command.upgrade)(config, target)

                await connection.run_sync(apply)

        for model in ("board", "board_media", "canvas", "canvas_feed", "asset", "tag", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        storage = LocalObjectStorage(tmp_path / "pg-media-files", 8 * 1024 * 1024)
        location = StorageLocation("e" * 64, {"provider": "local", "root": str(storage.root)})
        created = False
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migrate("0029_canvas_publications")
            r = await seed_legacy(test_db)
            before = await old_state(test_db)
            await migrate("0030_board_media")
            assert await old_state(test_db) == before
            await migrate("0029_canvas_publications", downgrade=True)
            assert await old_state(test_db) == before
            await migrate("0030_board_media")
            await storage.initialize()
            await exercise(test_db, r, storage, location)
            await cleanup_delete_races(test_db, r, storage, location)
            await upload_delete_races(test_db, r, storage, location)
            after = await old_state(test_db)
            with pytest.raises(RuntimeError, match="Board media or cleanup history remains"):
                await migrate("0029_canvas_publications", downgrade=True)
            assert await old_state(test_db) == after
            async with test_db() as db:
                assert (
                    await db.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0030_board_media"
                )
                assert (
                    await db.scalar(
                        text(
                            "SELECT data_type FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='board_media_assets' AND column_name='storage_location'"
                        )
                    )
                    == "jsonb"
                )
        finally:
            await storage.close()
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
