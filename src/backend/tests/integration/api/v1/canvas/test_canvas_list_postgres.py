"""Opt-in local PostgreSQL owner-list snapshot and shared lifecycle/policy scenarios."""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.models.board import BoardMember, BoardPolicy
from app.models.canvas import Canvas, CanvasDocument, CanvasPublication, CanvasPublicationCounter
from app.models.tag import CanvasTag
from tests.integration.api.v1.canvas.test_canvas_list import (
    AT,
    assert_lifecycle,
    assert_parity,
    assert_policy,
    assert_queries,
    ids,
    listing,
    seed_list,
    state,
)

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_snapshot(test_db, r, plan_path):
    entered, resume = asyncio.Event(), asyncio.Event()
    original = AsyncSession.execute
    canvas_id = UUID(int=900)
    plans = []

    async def observed(db, statement, *args, **kwargs):
        result = await original(db, statement, *args, **kwargs)
        if (
            "owner_boards AS" in str(statement)
            and "last_modified_at" in str(statement)
            and not entered.is_set()
        ):
            sql = str(
                statement.compile(dialect=db.bind.dialect, compile_kwargs={"literal_binds": True})
            )
            explain = await original(db, text("EXPLAIN (FORMAT JSON) " + sql))
            plans.extend(explain.scalar_one())
            entered.set()
            await resume.wait()
        return result

    task = None
    try:
        with patch.object(AsyncSession, "execute", observed):
            task = asyncio.create_task(listing(r))
            await asyncio.wait_for(entered.wait(), 5)
            async with test_db() as db:
                canvas = await db.get(Canvas, canvas_id)
                canvas.title = "동시 변경 초안"
                canvas.revision = 4
                canvas.updated_at = AT + timedelta(seconds=10)
                document = await db.get(CanvasDocument, canvas_id)
                document.revision = 3
                document.updated_at = AT + timedelta(seconds=11)
                publication = await db.get(CanvasPublication, canvas_id)
                publication.publication_revision = 2
                publication.source_metadata_revision = 4
                publication.source_document_revision = 3
                publication.published_at = AT + timedelta(seconds=12)
                (await db.get(CanvasPublicationCounter, canvas_id)).revision = 2
                await db.execute(delete(CanvasTag).where(CanvasTag.canvas_id == canvas_id))
                db.add(CanvasTag(canvas_id=canvas_id, tag_id=r.old.id))
                policy = await db.get(BoardPolicy, (r.boards[0].id, "create_canvas"))
                policy.min_grade_id = r.grades[0][2].id
                member = await db.get(BoardMember, (r.boards[0].id, r.writer.id))
                member.status = "banned"
                await db.commit()
            resume.set()
            previous = await asyncio.wait_for(task, 5)
        item = next(item for item in previous.items if item.canvas.id == canvas_id)
        assert item.canvas.title == "노출 금지 초안 제목" and item.canvas.revision == 3
        assert item.document_revision == 2 and item.last_modified_at == AT
        assert item.publication_revision == item.publication.publication_revision == 1
        assert [tag.id for tag in item.canvas.tags] == [r.new.id]
        assert item.capabilities.edit_document
        assert 900 not in ids(await listing(r))
        async with test_db() as db:
            (await db.get(BoardMember, (r.boards[0].id, r.writer.id))).status = "active"
            await db.commit()
        current = await listing(r)
        item = next(item for item in current.items if item.canvas.id == canvas_id)
        assert item.canvas.id == canvas_id and item.canvas.title == "동시 변경 초안"
        assert item.canvas.revision == 4 and item.document_revision == 3
        assert item.last_modified_at == AT + timedelta(seconds=11)
        assert item.publication_revision == item.publication.publication_revision == 2
        assert [tag.id for tag in item.canvas.tags] == [r.old.id]
        assert not item.capabilities.edit_document and item.capabilities.unpublish
        await assert_parity(r, current)
        plan_path.write_text(json.dumps(plans, ensure_ascii=False, indent=2))
        assert plans and plans[0]["Plan"]
        async with test_db() as db:
            assert (
                await db.scalar(
                    text(
                        "SELECT count(*) FROM pg_indexes WHERE schemaname=current_schema() AND indexname IN ('ix_canvases_author_id','ix_canvases_board_shelf')"
                    )
                )
                == 2
            )
    finally:
        resume.set()
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


def test_real_postgres_owner_list_policy_lifecycle_snapshot_and_preservation(monkeypatch, tmp_path):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_owner_list_test_" + uuid4().hex
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

        for model in ("board", "canvas", "canvas_feed", "canvas_list", "asset", "tag", "user"):
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
            r = await seed_list(test_db)
            await assert_queries(test_db, r)
            await assert_policy(test_db, r)
            await assert_lifecycle(test_db, r)
            await assert_snapshot(test_db, r, tmp_path / "canvas-owner-list-plan.json")
            before = await state(test_db)
            await listing(r, status="all")
            assert await state(test_db) == before
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
