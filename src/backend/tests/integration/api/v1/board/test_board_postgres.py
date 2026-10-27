"""Opt-in real PostgreSQL migrations and aggregate races, isolated from application tables."""

import asyncio
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardDeleteForm,
    BoardLayout,
    BoardMember,
    BoardMemberGrade,
)
from app.models.user import User
from app.services.board import BoardService

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


def test_real_migration_creation_race_and_downgrade(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_creation_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL, connect_args={"server_settings": {"search_path": schema}}
        )
        created = False

        async def migrate(target, downgrade=False):
            async with engine.begin() as connection:

                def apply(sync_connection):
                    config.attributes["connection"] = sync_connection
                    (command.downgrade if downgrade else command.upgrade)(config, target)

                await connection.run_sync(apply)

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        monkeypatch.setattr("app.services.board.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migrate("head")
            async with test_db() as db:
                user = User(
                    email="pg-board@example.com",
                    name="Board owner",
                    role="user",
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                await db.commit()
                user_id = user.id
            service = BoardService()
            form = BoardCreateForm(name="PG 보드", slug="same-address", interest_ids=["ai"])
            results = await asyncio.gather(
                service.create(user_id, form), service.create(user_id, form), return_exceptions=True
            )
            assert sum(not isinstance(result, Exception) for result in results) == 1
            failures = [result for result in results if isinstance(result, BoardException)]
            assert (
                len(failures) == 1
                and failures[0].code.error == BoardErrorCode.SLUG_TAKEN.code.error
            )
            board = next(result for result in results if not isinstance(result, Exception))
            home = await service.home(user_id, board_id=board.id)
            assert len(home.shelves) == 2 and home.membership.grade_name == "뉴커머"
            other = await service.create(user_id, BoardCreateForm(name="Other", slug="other-board"))
            async with test_db() as db:
                assert (
                    await db.scalar(
                        text("SELECT pg_typeof(document)::text FROM board_layouts LIMIT 1")
                    )
                    == "jsonb"
                )
                other_grade = await db.scalar(
                    select(BoardMemberGrade.id)
                    .where(BoardMemberGrade.board_id == other.id)
                    .limit(1)
                )
                with pytest.raises(IntegrityError):
                    await db.execute(
                        text("UPDATE board_members SET grade_id=:grade WHERE board_id=:board"),
                        {"grade": other_grade, "board": board.id},
                    )
                await db.rollback()
            # At 19 owned boards, two different concurrent creations must not exceed the limit.
            for index in range(17):
                await service.create(
                    user_id, BoardCreateForm(name=f"Quota {index}", slug=f"quota-{index}")
                )
            results = await asyncio.gather(
                *[
                    service.create(user_id, BoardCreateForm(name="Last", slug=f"last-{i}"))
                    for i in range(2)
                ],
                return_exceptions=True,
            )
            assert sum(not isinstance(result, Exception) for result in results) == 1
            assert any(
                isinstance(result, BoardException)
                and result.code.error == BoardErrorCode.LIMIT_REACHED.code.error
                for result in results
            )
            async with test_db() as db:
                assert await db.scalar(select(func.count()).select_from(Board)) == 20
            await service.delete_empty(
                user_id, board.id, BoardDeleteForm(expected_revision=0, confirm_slug=board.slug)
            )
            async with test_db() as db:
                assert await db.get(BoardLayout, board.id) is None
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(BoardMember)
                        .where(BoardMember.board_id == board.id)
                    )
                    == 0
                )
            await migrate("0023_broaden_interest_catalog", downgrade=True)
            async with test_db() as db:
                assert await db.scalar(text("SELECT to_regclass('boards')")) is None
                assert (
                    await db.scalar(select(User.email).where(User.id == user_id))
                    == "pg-board@example.com"
                )
            await migrate("head")
            async with test_db() as db:
                assert await db.scalar(select(func.count()).select_from(Board)) == 0
        finally:
            await engine.dispose()
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
            await admin.dispose()

    asyncio.run(run())
