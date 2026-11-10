"""Isolated PostgreSQL comment migration, CAS and deletion constraints."""

import asyncio
import os
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.canvas import Canvas
from app.models.canvas_comment import (
    CanvasComment,
    CommentCreateForm,
    CommentPatchForm,
    CommentRepository,
)
from app.models.user import User
from app.services.canvas_comment import CanvasCommentService
from tests.integration.api.v1.canvas.test_canvas_feed import seed_feed

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


def test_postgres_comments_migration_cas_orphan_and_canvas_cascade(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_comments_test_" + uuid4().hex
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
            await migrate("0031_canvas_likes")
            r = await seed_feed(test_db)
            cid = UUID(int=900)
            before = await r.canvas.get(None, cid)
            await migrate("0032_canvas_comments")
            assert await r.canvas.get(None, cid) == before
            service = CanvasCommentService(r.canvas.access, CommentRepository())
            row = await service.create(r.writer.id, cid, CommentCreateForm(body="원본"))
            results = await asyncio.gather(
                *[
                    service.change(
                        r.writer.id,
                        cid,
                        row.id,
                        CommentPatchForm(expected_revision=0, body=f"수정{i}"),
                    )
                    for i in range(2)
                ],
                return_exceptions=True,
            )
            assert sum(not isinstance(x, Exception) for x in results) == 1
            loser = next(x for x in results if isinstance(x, Exception))
            assert (
                isinstance(loser, CanvasException)
                and loser.code == CanvasErrorCode.COMMENT_CONFLICT.code
            )
            with pytest.raises(RuntimeError, match="refusing destructive downgrade"):
                await migrate("0031_canvas_likes", True)
            latest = await service.get(r.owner.id, cid, row.id)
            await service.change(
                r.owner.id,
                cid,
                row.id,
                CommentPatchForm(
                    expected_revision=latest.revision, status="hidden", reason="운영 검토"
                ),
            )
            async with test_db() as db:
                await db.execute(delete(User).where(User.id == r.writer.id))
                await db.commit()
                assert (await db.get(CanvasComment, row.id)).author_id is None
            with pytest.raises(CanvasException) as hidden:
                await service.get(None, cid, row.id)
            assert hidden.value.code == CanvasErrorCode.NOT_FOUND.code
            assert (await service.get(r.owner.id, cid, row.id)).status == "hidden"
            async with test_db() as db:
                await db.execute(delete(Canvas).where(Canvas.id == cid))
                await db.commit()
                assert await db.scalar(select(func.count()).select_from(CanvasComment)) == 0
            await migrate("0031_canvas_likes", True)
            await migrate("0032_canvas_comments")
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
