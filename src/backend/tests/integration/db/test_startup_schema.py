"""Runtime startup never creates pending ORM models ahead of an Alembic revision."""

import asyncio
import sqlite3
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config


@pytest.mark.primary_data
@pytest.mark.parametrize("legacy_create_all", [True, False])
def test_reload_with_pending_models_keeps_schema_owned_by_migrations(
    tmp_path, monkeypatch, legacy_create_all
):
    import app.core.db.session as database
    import app.main as main

    # Reproduce a reload between adding publication ORM models and writing their migration.
    path = tmp_path / "reload-schema.db"
    url = f"sqlite+aiosqlite:///{path}"
    monkeypatch.setattr(SETTINGS, "DATABASE_URL", url)
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "OAUTH_ENABLED", False)
    monkeypatch.setattr(main.RedisManager, "verify_startup", AsyncMock())
    monkeypatch.setattr(main.RedisManager, "close", AsyncMock())
    monkeypatch.setattr(main.MAIL_SERVICE, "initialize", AsyncMock())
    monkeypatch.setattr(main.BillingService, "initialize", AsyncMock())
    config = _build_alembic_config(url)
    pending_tables = {
        "canvas_publication_counters",
        "canvas_publications",
        "canvas_publication_tags",
    }
    assert pending_tables <= database.Base.metadata.tables.keys()

    async def old_migration_head(_url):
        await asyncio.to_thread(command.upgrade, config, "0028_canvas_tags")
        if legacy_create_all:
            await database.init_db()

    monkeypatch.setattr(main, "run_startup_schema_migrations", old_migration_head)
    engine = create_async_engine(url)
    monkeypatch.setattr(database, "_ENGINE", engine)
    monkeypatch.setattr(database, "_SESSION_FACTORY", None)

    async def start_and_stop():
        async with main.application_lifespan(FastAPI()):
            pass

    asyncio.run(start_and_stop())
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0028_canvas_tags",
        )
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        }
        if legacy_create_all:
            assert pending_tables <= tables
        else:
            assert pending_tables.isdisjoint(tables)
        connection.execute(
            "INSERT INTO users (id,email,name,is_active,is_verified,role,created_at,updated_at) VALUES (1,'reload@example.com','Preserved',1,1,'user',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        )

    if legacy_create_all:
        with pytest.raises(
            OperationalError, match="table canvas_publication_counters already exists"
        ):
            command.upgrade(config, "head")
        return
    # The later migration now owns table creation; no duplicate-table failure or silent stamp.
    command.upgrade(config, "head")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0033_board_subscriptions",
        )
        assert connection.execute("SELECT name FROM users WHERE id=1").fetchone() == ("Preserved",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
