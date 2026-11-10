"""Real local PostgreSQL isolated-schema layout locks, CAS, rollback and MVCC."""

import asyncio
import os
from contextlib import asynccontextmanager
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error import AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import Board, BoardMember, BoardPolicy, BoardTransaction
from app.models.canvas import CanvasPatchForm, CanvasPublishForm
from app.models.canvas_feed import CanvasFeedRepository
from app.models.user import User
from tests.integration.api.v1.board.test_board_layout import (
    assert_collection_bounds,
    assert_projection,
    assert_storage,
    form,
    services,
    state,
)

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_races(test_db, r):
    boards, layouts = services()
    board_id = r.boards[0].id
    current = await layouts.get(r.owner.id, board_id)
    docs = [current.document.model_dump(mode="json") for _ in range(2)]
    for index, document in enumerate(docs):
        document["widgets"][0]["position"]["x"] = index + 1
        # Remove the intentionally stale/deleted source before saving again.
        document["widgets"] = [
            w for w in document["widgets"] if w["id"] != "private-custom-secret-id"
        ]
    before = await state(test_db, board_id)
    results = await asyncio.gather(
        *[
            layouts.save(r.owner.id, board_id, form(document, current.layout_revision))
            for document in docs
        ],
        return_exceptions=True,
    )
    assert sum(not isinstance(value, Exception) for value in results) == 1
    assert (
        sum(
            isinstance(value, BoardException) and value.code == BoardErrorCode.LAYOUT_CONFLICT.code
            for value in results
        )
        == 1
    )
    after = await state(test_db, board_id)
    assert (
        after[1] == before[1] + 1 and after[2] == before[2] and len(after[3]) == len(before[3]) + 1
    )

    # Prove the writer waits on the common Board lock, then reads the revoked role.
    async with test_db() as db:
        (await db.get(BoardMember, (board_id, r.writer.id))).role = "admin"
        await db.commit()
    entered, pids = asyncio.Event(), []
    original_board = BoardTransaction.locked_board

    async def observed_board(tx, ident):
        pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
        entered.set()
        return await original_board(tx, ident)

    async with test_db() as blocker:
        await blocker.scalar(select(Board).where(Board.id == board_id).with_for_update())
        (await blocker.get(BoardMember, (board_id, r.writer.id))).role = "member"
        await blocker.flush()
        with patch.object(BoardTransaction, "locked_board", observed_board):
            pending = asyncio.create_task(
                layouts.save(r.writer.id, board_id, form(docs[0], after[1]))
            )
            try:
                await asyncio.wait_for(entered.wait(), 5)
                async with asyncio.timeout(5):
                    while True:
                        async with test_db() as observer:
                            waiting = await observer.scalar(
                                text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"),
                                {"pid": pids[0]},
                            )
                        if waiting:
                            break
                        assert not pending.done()
                        await asyncio.sleep(0.01)
                await blocker.commit()
                with pytest.raises(BoardException) as revoked:
                    await asyncio.wait_for(pending, 5)
                assert revoked.value.code == BoardErrorCode.FORBIDDEN.code
            finally:
                if not pending.done():
                    pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
    assert await state(test_db, board_id) == after

    # The reader has metadata/layout/account snapshot, but has not hydrated any header yet.
    baseline = await boards.home(r.writer.id, board_id=board_id)
    entered, release = asyncio.Event(), asyncio.Event()
    original_feed = CanvasFeedRepository.read_home

    async def paused_feed(repository, db, user_id, ident, sources):
        assert await db.scalar(text("SHOW transaction_isolation")) == "repeatable read"
        assert await db.scalar(text("SHOW transaction_read_only")) == "on"
        entered.set()
        await release.wait()
        return await original_feed(repository, db, user_id, ident, sources)

    task = None
    try:
        with patch.object(CanvasFeedRepository, "read_home", paused_feed):
            task = asyncio.create_task(boards.home(r.writer.id, board_id=board_id))
            await asyncio.wait_for(entered.wait(), 5)
            fresh = await layouts.get(r.owner.id, board_id)
            changed = deepcopy(fresh.document.model_dump(mode="json"))
            changed["widgets"][0]["position"]["x"] += 10
            await layouts.save(r.owner.id, board_id, form(changed, fresh.layout_revision))
            # Publish through the real current-policy path before tightening access.
            await r.canvas.change(
                r.writer.id,
                r.canvases[0].id,
                CanvasPatchForm(
                    expected_revision=3,
                    title="동시 새 공개 제목",
                    tag_ids=[r.new.id],
                ),
            )
            await r.canvas.publish(
                r.writer.id,
                r.canvases[0].id,
                CanvasPublishForm(
                    expected_metadata_revision=4,
                    expected_document_revision=2,
                    expected_publication_revision=1,
                ),
            )
            async with test_db() as db:
                (await db.get(Board, board_id)).description = "동시 새 보드 소개"
                policy = await db.get(BoardPolicy, (board_id, "read_canvas"))
                policy.audience, policy.min_grade_id = "members", r.grades[0][2].id
                policy.staff_bypass = False
                (await db.get(User, r.writer.id)).is_active = False
                await db.commit()
            release.set()
            old = await asyncio.wait_for(task, 5)
        assert old == baseline
        old_item = next(
            item
            for data in old.widget_data
            if data.type == "canvas_collection"
            for item in data.items
            if item.canvas.id.int == 900
        )
        assert old_item.canvas.title == "공개 제목 900" and old_item.canvas.tags[0].id == r.old.id
        with pytest.raises(AuthException):
            await boards.home(r.writer.id, board_id=board_id)
        newer = await boards.home(None, board_id=board_id)
        assert newer.layout_revision == old.layout_revision + 1
        assert newer.board.description == "동시 새 보드 소개"
        assert all(not data.items for data in newer.widget_data if data.type == "canvas_collection")
    finally:
        release.set()
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


def test_real_postgres_layout_locks_cas_snapshot_and_existing_data(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_layout_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL,
            connect_args={
                "server_settings": {
                    "search_path": schema,
                    "statement_timeout": "10000",
                }
            },
        )
        created = False

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        for model in ("board", "canvas", "canvas_feed", "asset", "tag", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            async with engine.begin() as connection:

                def migrate(sync):
                    config.attributes["connection"] = sync
                    command.upgrade(config, "head")

                await connection.run_sync(migrate)
            r = await assert_storage(test_db)
            await assert_projection(test_db, r)
            await assert_collection_bounds(test_db, r)
            await assert_races(test_db, r)
            async with test_db() as db:
                assert (
                    await db.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0032_canvas_comments"
                )
                assert (
                    await db.scalar(
                        text(
                            "SELECT data_type FROM information_schema.columns WHERE table_schema=current_schema() "
                            "AND table_name='board_layouts' AND column_name='document'"
                        )
                    )
                    == "jsonb"
                )
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
