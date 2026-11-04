"""Opt-in local PostgreSQL feed MVCC, real policy/keysets and schema isolation."""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.models.canvas import CanvasCreateForm, CanvasPatchForm, CanvasPublishForm
from tests.integration.api.v1.canvas.test_canvas_feed import (
    assert_feed_lifecycle,
    assert_feed_policy_parity,
    assert_feed_queries,
    listing,
    seed_feed,
)

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_statement_snapshot(test_db, r, plan_path):
    created = await r.canvas.create(
        r.owner.id,
        r.boards[0].id,
        CanvasCreateForm(
            shelf_id=r.shelves[0].id,
            title="이전 일관 공개본",
            visibility="public",
            tag_ids=[r.old.id],
        ),
    )
    canvas_id = created.canvas.id
    await r.canvas.publish(
        r.owner.id,
        canvas_id,
        CanvasPublishForm(
            expected_metadata_revision=0,
            expected_document_revision=0,
            expected_publication_revision=0,
        ),
    )
    entered, resume = asyncio.Event(), asyncio.Event()
    original = AsyncSession.execute
    plan = []

    async def observed(db, statement, *args, **kwargs):
        result = await original(db, statement, *args, **kwargs)
        if not entered.is_set() and "readable_boards AS" in str(statement):
            sql = str(
                statement.compile(dialect=db.bind.dialect, compile_kwargs={"literal_binds": True})
            )
            explain = await original(db, text("EXPLAIN (FORMAT JSON) " + sql))
            plan.extend(explain.scalar_one())
            entered.set()
            await resume.wait()
        return result

    task = None
    try:
        with patch.object(AsyncSession, "execute", observed):
            task = asyncio.create_task(listing(r))
            await asyncio.wait_for(entered.wait(), 5)
            # The reader has its statement result. A separate transaction can republish and
            # tighten visibility before Python assembles tags; its result must stay coherent.
            await r.canvas.change(
                r.owner.id,
                canvas_id,
                CanvasPatchForm(
                    expected_revision=0,
                    title="새로운 공개본",
                    visibility="members",
                    tag_ids=[r.new.id],
                ),
            )
            await r.canvas.publish(
                r.owner.id,
                canvas_id,
                CanvasPublishForm(
                    expected_metadata_revision=1,
                    expected_document_revision=0,
                    expected_publication_revision=1,
                ),
            )
            resume.set()
            previous = await asyncio.wait_for(task, 5)
        old = next(item for item in previous.items if item.canvas.id == canvas_id)
        assert old.canvas.title == "이전 일관 공개본" and old.canvas.visibility == "public"
        assert old.publication_revision == 1 and [tag.id for tag in old.canvas.tags] == [r.old.id]
        assert canvas_id not in [item.canvas.id for item in (await listing(r)).items]
        own = next(
            item for item in (await listing(r, r.owner.id)).items if item.canvas.id == canvas_id
        )
        assert own.canvas.title == "새로운 공개본" and own.publication_revision == 2
        assert [tag.id for tag in own.canvas.tags] == [r.new.id]
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
        assert plan and plan[0]["Plan"]
        async with test_db() as db:
            assert (
                await db.scalar(
                    text(
                        "SELECT count(*) FROM pg_indexes WHERE schemaname=current_schema() AND indexname IN ('ix_canvas_publications_published','ix_publication_tags_tag','ix_canvases_board_shelf')"
                    )
                )
                == 3
            )
    finally:
        resume.set()
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


def test_real_postgres_feed_keysets_policy_lifecycle_and_statement_snapshot(monkeypatch, tmp_path):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_feed_test_" + uuid4().hex
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
            r = await seed_feed(test_db)
            await assert_feed_queries(test_db, r)
            await assert_feed_policy_parity(test_db, r)
            await assert_feed_lifecycle(test_db, r)
            await assert_statement_snapshot(test_db, r, tmp_path / "canvas-feed-plan.json")
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
