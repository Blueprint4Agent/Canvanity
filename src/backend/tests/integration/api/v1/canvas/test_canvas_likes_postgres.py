"""Opt-in isolated PostgreSQL migration, uniqueness and actual lock contention."""

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import Board, BoardCreateForm, BoardMember, BoardRepository, BoardTransaction
from app.models.canvas import CanvasCreateForm, CanvasLike, CanvasPublishForm, CanvasRepository
from app.models.user import User
from app.services.board import BoardService
from app.services.board_permission import BoardPermissionService
from app.services.canvas import CanvasService
from app.services.canvas_access import CanvasAccessService
from app.services.canvas_like import CanvasLikeService
from tests.integration.api.v1.tag.test_tag_postgres import wait_until_blocked

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


def test_postgres_migration_idempotence_policy_race_and_cascade(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_likes_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL,
            connect_args={"server_settings": {"search_path": schema, "statement_timeout": "10000"}},
        )
        created, task = False, None

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        async def migration(target, *, downgrade=False):
            async with engine.begin() as connection:

                def migrate(sync):
                    config.attributes["connection"] = sync
                    (command.downgrade if downgrade else command.upgrade)(config, target)

                await connection.run_sync(migrate)

        for model in ("board", "canvas", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migration("0030_board_media")
            async with test_db() as db:
                owner, reader = [
                    User(
                        email=f"likes-{i}@example.com",
                        name=f"사용자{i}",
                        role="user",
                        is_active=True,
                        is_verified=True,
                    )
                    for i in range(2)
                ]
                db.add_all([owner, reader])
                await db.commit()
            permission = BoardPermissionService()
            boards = BoardService(permission, BoardRepository())
            board = await boards.create(
                owner.id, BoardCreateForm(name="좋아요 검증", slug="likes-test")
            )
            home = await boards.home(board_id=board.id, user_id=owner.id)
            async with test_db() as db:
                db.add(
                    BoardMember(
                        board_id=board.id,
                        user_id=reader.id,
                        role="member",
                        status="active",
                        grade_id=home.grades[0].id,
                    )
                )
                await db.commit()
            access = CanvasAccessService(permission)
            canvases = CanvasService(access, CanvasRepository())
            canvas = await canvases.create(
                owner.id,
                board.id,
                CanvasCreateForm(
                    shelf_id=next(s.id for s in home.shelves if s.is_default),
                    title="이전 자료",
                    visibility="public",
                ),
            )
            cid = canvas.canvas.id
            await canvases.publish(
                owner.id,
                cid,
                CanvasPublishForm(
                    expected_metadata_revision=0,
                    expected_document_revision=0,
                    expected_publication_revision=0,
                ),
            )
            before = await canvases.get(None, cid)
            await migration("head")
            assert await canvases.get(None, cid) == before
            likes = CanvasLikeService(access, CanvasRepository())
            results = await asyncio.gather(
                *[likes.set(reader.id, cid, liked=True) for _ in range(6)]
            )
            assert all(result.count == 1 and result.liked for result in results)
            async with test_db() as db:
                assert await db.scalar(select(func.count()).select_from(CanvasLike)) == 1
            with pytest.raises(IntegrityError):
                async with test_db() as db:
                    db.add(CanvasLike(canvas_id=cid, user_id=reader.id))
                    await db.commit()
            with pytest.raises(RuntimeError, match="refusing destructive downgrade"):
                await migration("0030_board_media", downgrade=True)
            results = await asyncio.gather(
                *[likes.set(reader.id, cid, liked=False) for _ in range(4)]
            )
            assert all(result.count == 0 and not result.liked for result in results)

            entered, pids = asyncio.Event(), []
            original = BoardTransaction.locked_board

            async def observed(tx, board_id):
                pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
                entered.set()
                return await original(tx, board_id)

            with patch.object(BoardTransaction, "locked_board", observed):
                async with test_db() as db:
                    row = await db.scalar(
                        select(Board).where(Board.id == board.id).with_for_update()
                    )
                    task = asyncio.create_task(likes.set(reader.id, cid, liked=True))
                    await asyncio.wait_for(entered.wait(), 5)
                    await wait_until_blocked(test_db, task, pids[0])
                    row.status = "archived"
                    await db.commit()
                with pytest.raises(CanvasException) as denied:
                    await task
                assert denied.value.code == CanvasErrorCode.FORBIDDEN.code
                task = None
            assert (await likes.get(None, cid)).count == 0
            async with test_db() as db:
                row = await db.get(Board, board.id)
                row.status = "active"
                await db.commit()
            await likes.set(reader.id, cid, liked=True)
            async with test_db() as db:
                await db.execute(delete(User).where(User.id == reader.id))
                await db.commit()
            assert (await likes.get(None, cid)).count == 0
            await migration("0030_board_media", downgrade=True)
            await migration("head")
            assert await canvases.get(None, cid) == before
        finally:
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
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
