"""Isolated PostgreSQL daily uniqueness, coherent real sources and retention."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import BoardMember
from app.models.canvas import Canvas, CanvasRepository
from app.models.canvas_comment import CommentCreateForm, CommentRepository
from app.models.canvas_stats import CanvasStatsRepository, CanvasView
from app.models.user import User
from app.services.canvas_comment import CanvasCommentService
from app.services.canvas_like import CanvasLikeService
from app.services.canvas_stats import CanvasStatsService, cleanup_canvas_views
from tests.integration.api.v1.canvas.test_canvas_feed import seed_feed

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


def test_postgres_stats_daily_race_window_current_access_and_cascades(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_stats_test_" + uuid4().hex
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

        async def migrate(target, downgrade=False):
            async with engine.begin() as connection:

                def apply(sync):
                    config.attributes["connection"] = sync
                    (command.downgrade if downgrade else command.upgrade)(config, target)

                await connection.run_sync(apply)

        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migrate("0033_board_subscriptions")
            r = await seed_feed(test_db)
            cid = UUID(int=900)
            before = await r.canvas.get(None, cid)
            await migrate("0034_canvas_views")
            service = CanvasStatsService(r.canvas.access, CanvasStatsRepository())
            assert (await service.get(None, cid)).activity_score == 0
            await CanvasLikeService(r.canvas.access, CanvasRepository()).set(
                r.writer.id, cid, liked=True
            )
            await CanvasCommentService(r.canvas.access, CommentRepository()).create(
                r.writer.id, cid, CommentCreateForm(body="집계 원본")
            )
            results = await asyncio.gather(*[service.record(r.reader.id, cid) for _ in range(6)])
            assert sum(item.recorded for item in results) == 1
            assert all(
                item.stats.view_count == 1 and item.stats.activity_score == 3 for item in results
            )
            assert await r.canvas.get(None, cid) == before
            at = datetime.now(UTC)
            async with test_db() as db:
                for offset in (31, 29, -1):
                    db.add(
                        CanvasView(
                            canvas_id=cid,
                            user_id=r.writer.id,
                            viewed_on=at.date() - timedelta(days=offset),
                        )
                    )
                await db.commit()
                columns = (
                    (
                        await db.execute(
                            text(
                                "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='canvas_views'"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                assert set(columns) == {"canvas_id", "user_id", "viewed_on"}
            with pytest.raises(RuntimeError, match="refusing destructive downgrade"):
                await migrate("0033_board_subscriptions", True)
            current = await service.get(None, cid)
            assert (
                current.view_count == 2
                and current.like_count == current.comment_count == 1
                and current.activity_score == 4
            )
            assert (
                await cleanup_canvas_views(repository=CanvasStatsRepository(), at=at, limit=1) == 1
            )
            assert (
                await cleanup_canvas_views(repository=CanvasStatsRepository(), at=at, limit=1) == 0
            )
            async with test_db() as db:
                member = await db.get(BoardMember, (r.boards[0].id, r.reader.id))
                member.status = "banned"
                await db.commit()
            for action in (service.get, service.record):
                with pytest.raises(CanvasException) as denied:
                    await action(r.reader.id, cid)
                assert denied.value.code == CanvasErrorCode.NOT_FOUND.code
            async with test_db() as db:
                await db.execute(delete(User).where(User.id == r.reader.id))
                await db.commit()
            assert (await service.get(None, cid)).view_count == 1
            async with test_db() as db:
                await db.execute(delete(Canvas).where(Canvas.id == cid))
                await db.commit()
                assert await db.scalar(select(func.count()).select_from(CanvasView)) == 0
            await migrate("0033_board_subscriptions", True)
            await migrate("0034_canvas_views")
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
