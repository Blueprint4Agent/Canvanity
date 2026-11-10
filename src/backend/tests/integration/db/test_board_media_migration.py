"""FK-enabled SQLite preserves a populated 0029 database and refuses destructive rollback."""

import asyncio
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.db.migrations import _build_alembic_config
from app.models.board_media import BoardMediaAsset, now
from tests.integration.api.v1.board.test_board_media_postgres import old_state, seed_legacy

pytestmark = pytest.mark.primary_data


def test_populated_sqlite_board_media_additive_upgrade_and_safe_downgrade(tmp_path, monkeypatch):
    url = f"sqlite+aiosqlite:///{tmp_path / 'media-migration.db'}"
    config = _build_alembic_config(url)

    async def run():
        engine = create_async_engine(url)

        @event.listens_for(engine.sync_engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        for model in ("board", "board_media", "canvas", "canvas_feed", "asset", "tag", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)

        async def migrate(target, downgrade=False):
            async with engine.begin() as connection:

                def apply(sync):
                    config.attributes["connection"] = sync
                    (command.downgrade if downgrade else command.upgrade)(config, target)

                await connection.run_sync(apply)

        try:
            await migrate("0029_canvas_publications")
            r = await seed_legacy(test_db)
            before = await old_state(test_db)
            await migrate("0030_board_media")
            assert await old_state(test_db) == before
            await migrate("0029_canvas_publications", downgrade=True)
            assert await old_state(test_db) == before
            await migrate("0030_board_media")
            from uuid import uuid4

            asset_id = uuid4()
            async with test_db() as db:
                db.add(
                    BoardMediaAsset(
                        id=asset_id,
                        board_id=r.boards[0].id,
                        slot="cover",
                        owner_id=r.writer.id,
                        object_key=f"board-media/{asset_id}/{uuid4().hex}.webp",
                        storage_fingerprint="e" * 64,
                        storage_location={"provider": "local", "root": "/test-only"},
                        byte_size=1,
                        width=1,
                        height=1,
                        frame_count=1,
                        sha256="f" * 64,
                        state="pending",
                        upload_deadline=now(),
                    )
                )
                await db.commit()
            with pytest.raises(RuntimeError, match="Board media or cleanup history remains"):
                await migrate("0029_canvas_publications", downgrade=True)
            assert await old_state(test_db) == before
            async with test_db() as db:
                assert (
                    await db.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0030_board_media"
                )
                assert await db.get(BoardMediaAsset, asset_id) is not None
                assert (await db.execute(text("PRAGMA foreign_key_check"))).all() == []
        finally:
            await engine.dispose()

    asyncio.run(run())
