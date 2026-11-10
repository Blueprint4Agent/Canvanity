"""Real PostgreSQL subscription uniqueness, selected-feed scope and deletion."""

import asyncio
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import BoardMember, BoardRepository, BoardSubscription
from app.models.canvas_feed import CanvasFeedQuery
from app.models.user import User
from app.services.board_permission import BoardPermissionService
from app.services.board_subscription import BoardSubscriptionService
from tests.integration.api.v1.canvas.test_canvas_feed import ids, seed_feed

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


def test_postgres_subscriptions_selected_feed_race_cursor_and_cascade(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_subscriptions_test_" + uuid4().hex
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
            await migrate("0032_canvas_comments")
            r = await seed_feed(test_db)
            before = await r.feed.list(None, CanvasFeedQuery(), scope="plaza")
            await migrate("0033_board_subscriptions")
            assert await r.feed.list(None, CanvasFeedQuery(), scope="plaza") == before
            service = BoardSubscriptionService(BoardPermissionService(), BoardRepository())
            reader = r.reader.id
            results = await asyncio.gather(
                *[service.set(reader, r.boards[0].id, subscribed=True) for _ in range(5)]
            )
            assert all(item.subscribed for item in results)
            async with test_db() as db:
                assert await db.scalar(select(func.count()).select_from(BoardSubscription)) == 1
            with pytest.raises(RuntimeError, match="refusing destructive downgrade"):
                await migrate("0032_canvas_comments", True)
            await service.set(reader, r.boards[1].id, subscribed=True)
            first = await r.feed.list(
                reader, CanvasFeedQuery(limit=1), scope="unused", subscribed=True
            )
            assert first.next_cursor and ids(first) == [991]
            with pytest.raises(CanvasException) as wrong_user:
                await r.feed.list(
                    r.writer.id,
                    CanvasFeedQuery(cursor=first.next_cursor),
                    scope="unused",
                    subscribed=True,
                )
            assert wrong_user.value.code == CanvasErrorCode.INVALID_CURSOR.code
            async with test_db() as db:
                member = await db.get(BoardMember, (r.boards[0].id, reader))
                member.status = "banned"
                await db.commit()
            after = await r.feed.list(
                reader, CanvasFeedQuery(cursor=first.next_cursor), scope="unused", subscribed=True
            )
            assert ids(after) == [800]
            async with test_db() as db:
                await db.execute(delete(User).where(User.id == reader))
                await db.commit()
                assert await db.scalar(select(func.count()).select_from(BoardSubscription)) == 0
            await migrate("0032_canvas_comments", True)
            await migrate("0033_board_subscriptions")
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
