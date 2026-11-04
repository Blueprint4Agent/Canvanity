"""Opt-in real PostgreSQL tag uniqueness, metadata/permission races and preservation."""

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.asset import Asset, AssetDeletionOutbox, CanvasAssetRef
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardMember,
    BoardMemberGrade,
    BoardRepository,
    BoardTransaction,
    Shelf,
)
from app.models.canvas import (
    Canvas,
    CanvasCreateForm,
    CanvasDocument,
    CanvasPatchForm,
    CanvasRepository,
    utc_now,
)
from app.models.tag import (
    CanvasTag,
    Tag,
    TagCreateForm,
    TagRepository,
    TagSearchQuery,
    TagTransaction,
)
from app.models.user import User
from app.services.board import BoardService
from app.services.board_permission import BoardPermissionService
from app.services.canvas import CanvasService
from app.services.canvas_access import CanvasAccessService
from tests.fixtures.canvas_document_data import canvas_document

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def content_state(test_db):
    async with test_db() as db:
        return [
            [
                tuple(getattr(row, column.name) for column in model.__table__.columns)
                for row in (
                    await db.scalars(select(model).order_by(*model.__table__.primary_key.columns))
                ).all()
            ]
            for model in (Canvas, CanvasDocument, Asset, CanvasAssetRef, AssetDeletionOutbox)
        ]


async def wait_until_blocked(test_db, task, pid):
    async with asyncio.timeout(5):
        while True:
            async with test_db() as db:
                if await db.scalar(
                    text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": pid}
                ):
                    return
            assert not task.done(), "The competing transaction did not wait for its row lock"
            await asyncio.sleep(0.01)


async def seed_existing_content(test_db):
    async with test_db() as db:
        owner, writer = [
            User(
                email=f"pg-tag-{name}@example.com",
                name=name,
                role="user",
                is_active=True,
                is_verified=True,
            )
            for name in ("owner", "writer")
        ]
        db.add_all([owner, writer])
        await db.commit()
    boards = BoardService(BoardPermissionService(), BoardRepository())
    first = await boards.create(
        owner.id, BoardCreateForm(name="태그 이전 보드", slug="tag-existing")
    )
    other = await boards.create(owner.id, BoardCreateForm(name="다른 보드", slug="tag-other"))
    # The fixture intentionally seeds an older migration without calling current-schema reads.
    async with test_db() as db:
        shelf = await db.scalar(
            select(Shelf.id).where(Shelf.board_id == first.id, Shelf.is_default.is_(True))
        )
        grades = list(
            (
                await db.scalars(
                    select(BoardMemberGrade)
                    .where(BoardMemberGrade.board_id == first.id)
                    .order_by(BoardMemberGrade.rank)
                )
            ).all()
        )
        db.add(
            BoardMember(
                board_id=first.id,
                user_id=writer.id,
                role="member",
                grade_id=grades[1].id,
                status="active",
            )
        )
        canvas = Canvas(
            board_id=first.id, shelf_id=shelf, author_id=writer.id, title="보존할 캔버스"
        )
        db.add(canvas)
        await db.flush()
        asset_id = uuid4()
        location = {"provider": "local", "root": "/test-only-no-files"}
        db.add_all(
            [
                CanvasDocument(canvas_id=canvas.id, document=canvas_document(asset_id), revision=4),
                Asset(
                    id=asset_id,
                    board_id=first.id,
                    canvas_id=canvas.id,
                    owner_id=writer.id,
                    object_key="tag-migration.webp",
                    storage_fingerprint="c" * 64,
                    storage_location=location,
                    byte_size=10,
                    width=1,
                    height=1,
                    frame_count=1,
                    sha256="d" * 64,
                    state="ready",
                    upload_deadline=utc_now(),
                ),
                AssetDeletionOutbox(
                    asset_id=asset_id,
                    board_id=first.id,
                    object_key="tag-migration.webp",
                    storage_fingerprint="c" * 64,
                    storage_location=location,
                    reason="unused",
                    state="protected",
                    available_at=utc_now(),
                ),
            ]
        )
        await db.flush()
        db.add(
            CanvasAssetRef(canvas_id=canvas.id, asset_id=asset_id, board_id=first.id, scope="draft")
        )
        await db.commit()
    return owner, writer, first, other, canvas, grades


async def assert_tag_transactions(test_db, seed):
    owner, writer, board, other, canvas, grades = seed
    tags = TagRepository()
    service = CanvasService(CanvasAccessService(BoardPermissionService()), CanvasRepository())
    results = await asyncio.gather(
        *[
            tags.get_or_create(writer.id, TagCreateForm(name=name))
            for name in ["Straße", "STRASSE", " strasse ", "straße"]
        ]
    )
    assert sum(item.created for item in results) == 1
    assert len({item.tag.id for item in results}) == len({item.tag.name for item in results}) == 1
    common = results[0].tag
    second = (await tags.get_or_create(owner.id, TagCreateForm(name="한글"))).tag
    third = (await tags.get_or_create(owner.id, TagCreateForm(name="C++"))).tag
    composed = await tags.get_or_create(writer.id, TagCreateForm(name="가"))
    assert (await tags.get_or_create(owner.id, TagCreateForm(name="가"))).tag == composed.tag
    assert (await tags.search(TagSearchQuery(q="STRASSE"))).items == [common]
    literal = (await tags.get_or_create(writer.id, TagCreateForm(name="100%_"))).tag
    assert (await tags.search(TagSearchQuery(q="%_"))).items == [literal]
    async with test_db() as db:
        assert (
            await db.scalar(
                text("SELECT normalized_name FROM tags WHERE id=:id"), {"id": common.id}
            )
            == "strasse"
        )
        db.add(Tag(id=uuid4(), name="collision", normalized_name="strasse"))
        with pytest.raises(IntegrityError):
            await db.commit()
    before = await content_state(test_db)

    async def change(revision, tag_ids, **fields):
        return await service.change(
            writer.id,
            canvas.id,
            CanvasPatchForm(expected_revision=revision, tag_ids=tag_ids, **fields),
        )

    raced = await asyncio.gather(
        change(0, [common.id, second.id], title="첫 경쟁"),
        change(0, [common.id, third.id], title="두 번째 경쟁"),
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in raced) == 1, raced
    loser = next(item for item in raced if isinstance(item, Exception))
    assert isinstance(loser, CanvasException) and loser.code == CanvasErrorCode.CONFLICT.code
    assert loser.details == {"current_revision": 1}
    winner = next(item for item in raced if not isinstance(item, Exception))
    assert winner.canvas.revision == 1 and winner.document_revision == 4
    assert (await content_state(test_db))[1:] == before[1:]
    ids = [item.id for item in winner.canvas.tags]
    assert (await change(1, list(reversed(ids)))).canvas == winner.canvas
    with pytest.raises(CanvasException) as stale:
        await change(0, ids)
    assert stale.value.code == CanvasErrorCode.CONFLICT.code
    before = await content_state(test_db)
    before_links = winner.canvas.tags
    with pytest.raises(CanvasException) as missing:
        await change(1, [uuid4()], title="rollback")
    assert missing.value.code == CanvasErrorCode.INVALID_TAGS.code
    assert await content_state(test_db) == before
    original_replace = TagTransaction.replace_canvas_tags

    async def invalid_fk(tx, canvas_id, tag_ids):
        await original_replace(tx, canvas_id, tag_ids)
        tx._db.add(CanvasTag(canvas_id=canvas_id, tag_id=uuid4()))
        await tx._db.flush()

    for target, options in [
        ("app.models.tag.TagTransaction.replace_canvas_tags", {"new": invalid_fk}),
        (
            "sqlalchemy.ext.asyncio.AsyncSession.commit",
            {"side_effect": SQLAlchemyError("commit failed")},
        ),
    ]:
        with patch(target, **options):
            with pytest.raises(CanvasException) as failure:
                await change(1, [third.id], title="실패한 수정")
        assert failure.value.code == CanvasErrorCode.UNAVAILABLE.code
        assert await content_state(test_db) == before
        assert (await service.get(writer.id, canvas.id)).canvas.tags == before_links

    other_home = await BoardService(BoardPermissionService(), BoardRepository()).home(
        owner.id, board_id=other.id
    )
    reused = await service.create(
        owner.id,
        other.id,
        CanvasCreateForm(
            shelf_id=next(s.id for s in other_home.shelves if s.is_default),
            title="다른 보드에서도 재사용",
            tag_ids=[common.id],
        ),
    )
    assert reused.canvas.tags == [common]
    other_before = await service.get(owner.id, reused.canvas.id)
    with pytest.raises(CanvasException):
        await service.create(
            owner.id,
            other.id,
            CanvasCreateForm(
                shelf_id=reused.canvas.shelf_id, title="거부할 생성", tag_ids=[uuid4()]
            ),
        )
    assert await service.get(owner.id, reused.canvas.id) == other_before

    # Observe real lock waiting before the administrator commits a grade revocation.
    entered, pids = asyncio.Event(), []
    original_board = BoardTransaction.locked_board

    async def observed_board(tx, board_id):
        pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
        entered.set()
        return await original_board(tx, board_id)

    async with test_db() as blocker:
        await blocker.scalar(select(Board).where(Board.id == board.id).with_for_update())
        (await blocker.get(BoardMember, (board.id, writer.id))).grade_id = grades[0].id
        await blocker.flush()
        before = await content_state(test_db)
        with patch.object(BoardTransaction, "locked_board", new=observed_board):
            pending = asyncio.create_task(change(1, [second.id]))
            try:
                await asyncio.wait_for(entered.wait(), 5)
                await wait_until_blocked(test_db, pending, pids[0])
                await blocker.commit()
                with pytest.raises(CanvasException) as forbidden:
                    await asyncio.wait_for(pending, 5)
                assert forbidden.value.code == CanvasErrorCode.FORBIDDEN.code
            finally:
                if not pending.done():
                    pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
        assert await content_state(test_db) == before
    # The Tag mutation must recheck active status after its shared User lock actually waits.
    entered, pids = asyncio.Event(), []
    original_scalar = AsyncSession.scalar

    async def observed_user(db, statement, *args, **kwargs):
        descriptions = getattr(statement, "column_descriptions", [])
        if descriptions and descriptions[0].get("entity") is User:
            pids.append(await original_scalar(db, text("SELECT pg_backend_pid()")))
            entered.set()
        return await original_scalar(db, statement, *args, **kwargs)

    async with test_db() as blocker:
        user = await blocker.scalar(select(User).where(User.id == writer.id).with_for_update())
        user.is_active = False
        await blocker.flush()
        with patch.object(AsyncSession, "scalar", new=observed_user):
            pending = asyncio.create_task(
                tags.get_or_create(writer.id, TagCreateForm(name="inactive"))
            )
            try:
                await asyncio.wait_for(entered.wait(), 5)
                await wait_until_blocked(test_db, pending, pids[0])
                await blocker.commit()
                with pytest.raises(AuthException) as inactive:
                    await asyncio.wait_for(pending, 5)
                assert inactive.value.code == AuthErrorCode.USER_NOT_FOUND.code
            finally:
                if not pending.done():
                    pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
    assert (await tags.search(TagSearchQuery(q="inactive"))).items == []
    async with test_db() as db:
        for bad in [
            CanvasTag(canvas_id=canvas.id, tag_id=uuid4()),
            CanvasTag(canvas_id=uuid4(), tag_id=common.id),
        ]:
            db.add(bad)
            with pytest.raises(IntegrityError):
                await db.commit()
            await db.rollback()
        await db.execute(delete(User).where(User.id == writer.id))
        await db.commit()
    async with test_db() as db:
        assert (await db.get(Canvas, canvas.id)).author_id is None
        assert (await db.get(Tag, common.id)).name == common.name
        # Deleting the asset-free Canvas cascades only its link, retaining the dictionary.
        await db.execute(delete(Canvas).where(Canvas.id == reused.canvas.id))
        await db.commit()
        assert await db.get(CanvasTag, (reused.canvas.id, common.id)) is None
        assert await db.get(Tag, common.id) is not None


def test_real_postgres_tag_race_metadata_cas_permissions_and_populated_migration(monkeypatch):
    url = make_url(SETTINGS.DATABASE_URL)
    assert url.drivername == "postgresql+asyncpg" and url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "canvanity_tag_test_" + uuid4().hex
    config = _build_alembic_config(SETTINGS.DATABASE_URL)

    async def run():
        admin = create_async_engine(SETTINGS.DATABASE_URL)
        engine = create_async_engine(
            SETTINGS.DATABASE_URL, connect_args={"server_settings": {"search_path": schema}}
        )
        created = False

        @asynccontextmanager
        async def test_db():
            async with AsyncSession(engine, expire_on_commit=False) as db:
                yield db

        async def migrate(target):
            async with engine.begin() as connection:

                def apply(sync_connection):
                    config.attributes["connection"] = sync_connection
                    command.upgrade(config, target)

                await connection.run_sync(apply)

        for model in ("board", "canvas", "tag", "asset", "user"):
            monkeypatch.setattr(f"app.models.{model}.get_db", test_db)
        try:
            async with admin.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                created = True
            await migrate("0027_canvas_assets")
            seed = await seed_existing_content(test_db)
            before = await content_state(test_db)
            await migrate("head")
            assert await content_state(test_db) == before
            async with test_db() as db:
                assert (
                    await db.scalar(text("SELECT version_num FROM alembic_version"))
                    == "0030_board_media"
                )
            await assert_tag_transactions(test_db, seed)
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
