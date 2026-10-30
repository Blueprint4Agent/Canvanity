"""Opt-in real PostgreSQL migrations and aggregate races, isolated from application tables."""

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.core.config.settings import SETTINGS
from app.core.db.migrations import _build_alembic_config
from app.core.error import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    Board,
    BoardCreateForm,
    BoardDeleteForm,
    BoardGradeCreateForm,
    BoardGradeDeleteForm,
    BoardGradeOrderForm,
    BoardGradePatchForm,
    BoardLayout,
    BoardMember,
    BoardMemberAudit,
    BoardMemberGrade,
    BoardMemberInviteForm,
    BoardMemberPatchForm,
    BoardOwnershipTransferForm,
    BoardRepository,
    BoardSettingsPatchForm,
    BoardTransaction,
    Shelf,
    ShelfPolicy,
)
from app.models.user import User, Users
from app.services.board import BoardService
from app.services.board_grade import BoardGradeService
from app.services.board_membership import BoardMembershipService
from app.services.board_permission import BoardPermissionService

pytestmark = [
    pytest.mark.primary_data,
    pytest.mark.skipif(
        os.environ.get("CANVANITY_TEST_POSTGRES") != "1",
        reason="explicit local PostgreSQL probe only",
    ),
]


async def assert_grade_management(test_db, user_id, board_id):
    service = BoardGradeService(BoardPermissionService(), BoardRepository())
    initial = await service.list(user_id, board_id)
    first, second, third = [g.id for g in initial.items]
    changes = await asyncio.gather(
        *[
            service.change(
                user_id,
                board_id,
                grade_id,
                BoardGradePatchForm(
                    expected_revision=initial.board_revision,
                    reason="동시 기본값 변경",
                    is_default=True,
                ),
            )
            for grade_id in (second, third)
        ],
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in changes) == 1
    assert (
        sum(
            isinstance(item, BoardException)
            and item.code.error == BoardErrorCode.CONFLICT.code.error
            for item in changes
        )
        == 1
    )
    current = await service.list(user_id, board_id)
    assert current.board_revision == initial.board_revision + 1
    assert sum(g.is_default for g in current.items) == 1
    async with test_db() as db:
        # Both the default and rank constraints remain immediate throughout the operations.
        non_default = next(g.id for g in current.items if not g.is_default)
        with pytest.raises(IntegrityError):
            await db.execute(
                text("UPDATE board_member_grades SET is_default=true WHERE id=:id"),
                {"id": non_default},
            )
        await db.rollback()
        with pytest.raises(IntegrityError):
            await db.execute(
                text("UPDATE board_member_grades SET rank=0 WHERE id=:id"), {"id": second}
            )
        await db.rollback()
        shelf_id = await db.scalar(
            select(Shelf.id).where(Shelf.board_id == board_id, Shelf.slug == "general")
        )
        db.add(
            ShelfPolicy(
                board_id=board_id,
                shelf_id=shelf_id,
                action="read_canvas",
                audience="members",
                min_grade_id=first,
                staff_only=False,
                staff_bypass=True,
            )
        )
        await db.commit()
    added = await service.create(
        user_id,
        board_id,
        BoardGradeCreateForm(
            expected_revision=current.board_revision,
            reason="정수 최대 순위",
            name="최상위",
            rank=2**31 - 1,
        ),
    )
    ids = [added.grade.id, third, second, first]
    reordered = await service.reorder(
        user_id,
        board_id,
        BoardGradeOrderForm(
            expected_revision=added.board_revision,
            reason="유니크 순위 교환",
            grade_ids=ids,
        ),
    )
    assert [g.id for g in reordered.items] == ids and [g.rank for g in reordered.items] == [
        0,
        10,
        20,
        30,
    ]
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        with pytest.raises(BoardException) as rejected:
            await service.delete(
                user_id,
                board_id,
                first,
                BoardGradeDeleteForm(
                    expected_revision=reordered.board_revision,
                    reason="롤백 검증",
                    replacement_grade_id=second,
                ),
            )
        assert rejected.value.code.error == BoardErrorCode.UNAVAILABLE.code.error
    assert await service.list(user_id, board_id) == reordered
    async with test_db() as db:
        assert all(
            m.grade_id == first
            for m in (
                await db.scalars(select(BoardMember).where(BoardMember.board_id == board_id))
            ).all()
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMemberAudit)
                .where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "grade_deleted",
                )
            )
            == 0
        )
    # Delete the current default and prove all reference scopes move in the same transaction.
    selected = await service.change(
        user_id,
        board_id,
        first,
        BoardGradePatchForm(
            expected_revision=reordered.board_revision,
            reason="삭제 전 기본값",
            is_default=True,
        ),
    )
    deleted = await service.delete(
        user_id,
        board_id,
        first,
        BoardGradeDeleteForm(
            expected_revision=selected.board_revision,
            reason="참조 대체",
            replacement_grade_id=second,
        ),
    )
    assert next(g for g in deleted.items if g.id == second).is_default
    async with test_db() as db:
        assert await db.get(BoardMemberGrade, first) is None
        assert all(
            m.grade_id == second
            for m in (
                await db.scalars(select(BoardMember).where(BoardMember.board_id == board_id))
            ).all()
        )
        assert (
            await db.scalar(
                text(
                    "SELECT count(*) FROM board_policies WHERE board_id=:board AND min_grade_id=:grade"
                ),
                {"board": board_id, "grade": first},
            )
            == 0
        )
        assert (
            await db.scalar(
                select(ShelfPolicy.min_grade_id).where(
                    ShelfPolicy.board_id == board_id, ShelfPolicy.action == "read_canvas"
                )
            )
            == second
        )
        audit = await db.scalar(
            select(BoardMemberAudit).where(
                BoardMemberAudit.board_id == board_id, BoardMemberAudit.action == "grade_deleted"
            )
        )
        assert audit.changes["reassigned_members"] == 2
        assert (
            audit.changes["reassigned_board_policies"] > 0
            and audit.changes["reassigned_shelf_policies"] == 1
        )


async def assert_member_invitations(test_db, user_id, board_id):
    service = BoardMembershipService(BoardPermissionService(), BoardRepository())
    boards = BoardService(BoardPermissionService(), BoardRepository())
    async with test_db() as db:
        board = await db.get(Board, board_id)
        board.visibility, board.join_policy = "private", "invite"
        target = User(
            email="pg-invite@example.com",
            name="Invitee",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(target)
        await db.commit()
        target_id = target.id
    home = await boards.home(user_id, board_id=board_id)
    default_id = next(g.id for g in home.grades if g.is_default)
    form = BoardMemberInviteForm(
        user_id=target_id, expected_revision=home.board.revision, reason="동시 수동 초대"
    )
    results = await asyncio.gather(
        service.invite(user_id, board_id, form),
        service.invite(user_id, board_id, form),
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in results) == 1
    assert (
        sum(
            isinstance(item, BoardException)
            and item.code.error == BoardErrorCode.CONFLICT.code.error
            for item in results
        )
        == 1
    )
    result = next(item for item in results if not isinstance(item, Exception))
    assert result.member.role == "member" and result.member.grade_id == default_id
    assert result.board_revision == home.board.revision + 1
    repeated = await service.invite(
        user_id, board_id, form.model_copy(update={"expected_revision": result.board_revision})
    )
    assert repeated == result
    async with test_db() as db:
        rows = (
            await db.scalars(
                select(BoardMemberAudit).where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "member_invited",
                )
            )
        ).all()
        assert (
            len(rows) == 1
            and rows[0].actor_user_id == user_id
            and rows[0].target_user_id == target_id
        )
    await service.leave(target_id, board_id)

    # Observe PostgreSQL's actual blocker PID rather than infer locking from a delay.
    for operation in ("deactivate", "delete"):
        async with test_db() as db:
            target = User(
                email=f"pg-invite-{operation}@example.com",
                name="Racing target",
                role="user",
                is_active=True,
                is_verified=True,
            )
            db.add(target)
            await db.commit()
            target_id = target.id
        before = await boards.home(user_id, board_id=board_id)
        entered = asyncio.Event()
        pids = []
        original = BoardTransaction.lock_active_user

        async def observed(
            tx,
            target_user_id,
            *,
            observed_pids=pids,
            observed_entered=entered,
            observed_original=original,
        ):
            observed_pids.append(await tx._db.scalar(text("SELECT pg_backend_pid()")))
            observed_entered.set()
            return await observed_original(tx, target_user_id)

        async with test_db() as blocker:
            target = await blocker.scalar(
                select(User).where(User.id == target_id).with_for_update()
            )
            if operation == "delete":
                await blocker.delete(target)
            else:
                target.is_active = False
            await blocker.flush()
            with patch.object(BoardTransaction, "lock_active_user", new=observed):
                pending = asyncio.create_task(
                    service.invite(
                        user_id,
                        board_id,
                        BoardMemberInviteForm(
                            user_id=target_id,
                            expected_revision=before.board.revision,
                            reason="계정 상태 경쟁",
                        ),
                    )
                )
                try:
                    async with asyncio.timeout(5):
                        await entered.wait()
                        while True:
                            async with test_db() as observer:
                                blocked = await observer.scalar(
                                    text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"),
                                    {"pid": pids[0]},
                                )
                            if blocked:
                                break
                            assert not pending.done(), (
                                "Invitee check did not wait for the account row lock"
                            )
                            await asyncio.sleep(0.01)
                    await blocker.commit()
                    with pytest.raises(BoardException) as rejected:
                        await asyncio.wait_for(pending, timeout=5)
                    assert rejected.value.code.error == BoardErrorCode.INVITEE_NOT_FOUND.code.error
                finally:
                    if not pending.done():
                        pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)
        async with test_db() as db:
            assert await db.get(BoardMember, (board_id, target_id)) is None
            assert (await db.get(Board, board_id)).revision == before.board.revision
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(BoardMemberAudit)
                    .where(
                        BoardMemberAudit.board_id == board_id,
                        BoardMemberAudit.target_user_id == target_id,
                    )
                )
                == 0
            )


async def assert_board_settings(test_db, user_id, board_id, member_id):
    service = BoardService(BoardPermissionService(), BoardRepository())
    before = await service.home(user_id, board_id=board_id)
    member_before = await service.home(member_id, board_id=board_id)
    assert len(member_before.shelves) == 2
    results = await asyncio.gather(
        *[
            service.update(
                user_id,
                board_id,
                BoardSettingsPatchForm(
                    expected_revision=before.board.revision,
                    reason="동시 보드 설정",
                    name=f"설정 {index}",
                    interest_ids=ids,
                ),
            )
            for index, ids in enumerate((["ai"], ["development", "ai"]))
        ],
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in results) == 1
    assert (
        sum(
            isinstance(item, BoardException)
            and item.code.error == BoardErrorCode.CONFLICT.code.error
            for item in results
        )
        == 1
    )
    winner = next(item for item in results if not isinstance(item, Exception))
    saved = await service.home(user_id, board_id=board_id)
    assert saved.board == winner.board and saved.board.revision == before.board.revision + 1
    async with test_db() as db:
        audits = (
            await db.scalars(
                select(BoardMemberAudit).where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "board_updated",
                )
            )
        ).all()
        assert (
            len(audits) == 1
            and audits[0].changes["after"]["interest_ids"] == winner.board.interest_ids
        )
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        with pytest.raises(BoardException) as rejected:
            await service.update(
                user_id,
                board_id,
                BoardSettingsPatchForm(
                    expected_revision=winner.board_revision,
                    reason="설정 롤백",
                    name="저장 실패",
                    interest_ids=[],
                    visibility="public",
                    status="archived",
                ),
            )
        assert rejected.value.code.error == BoardErrorCode.UNAVAILABLE.code.error
    assert await service.home(user_id, board_id=board_id) == saved
    async with test_db() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMemberAudit)
                .where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "board_updated",
                )
            )
            == 1
        )
    archived = await service.update(
        user_id,
        board_id,
        BoardSettingsPatchForm(
            expected_revision=winner.board_revision,
            reason="보관",
            status="archived",
        ),
    )
    with pytest.raises(BoardException) as rejected:
        await service.update(
            user_id,
            board_id,
            BoardSettingsPatchForm(
                expected_revision=archived.board_revision,
                reason="복원 없는 변경",
                name="거부",
            ),
        )
    assert rejected.value.code.error == BoardErrorCode.FORBIDDEN.code.error
    public = await service.update(
        user_id,
        board_id,
        BoardSettingsPatchForm(
            expected_revision=archived.board_revision,
            reason="명시적 복원/공개",
            status="active",
            visibility="public",
        ),
    )
    # The general Shelf has an explicit members read policy from the grade probe.
    anonymous = await service.home(None, board_id=board_id)
    assert len(anonymous.shelves) == 1 and anonymous.shelves[0].slug == "notice"
    private = await service.update(
        user_id,
        board_id,
        BoardSettingsPatchForm(
            expected_revision=public.board_revision,
            reason="비공개",
            visibility="private",
            join_policy="invite",
        ),
    )
    member_after = await service.home(member_id, board_id=board_id)
    assert len(member_after.shelves) == 2 and member_after.membership == member_before.membership
    repeated = await service.update(
        user_id,
        board_id,
        BoardSettingsPatchForm(
            expected_revision=private.board_revision,
            reason="동일 값",
            name=private.board.name,
        ),
    )
    assert repeated == private


async def assert_board_lifecycle(test_db, owner_id, board_id, target_id):
    service = BoardService(BoardPermissionService(), BoardRepository())
    before = await service.home(owner_id, board_id=board_id)
    form = BoardOwnershipTransferForm(
        expected_revision=before.board.revision, target_user_id=target_id, reason="PG 소유권 위임"
    )
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        with pytest.raises(BoardException) as rejected:
            await service.transfer_ownership(owner_id, board_id, form)
        assert rejected.value.code.error == BoardErrorCode.UNAVAILABLE.code.error
    assert await service.home(owner_id, board_id=board_id) == before
    results = await asyncio.gather(
        service.transfer_ownership(owner_id, board_id, form),
        service.transfer_ownership(owner_id, board_id, form),
        return_exceptions=True,
    )
    assert sum(not isinstance(item, Exception) for item in results) == 1
    assert (
        sum(
            isinstance(item, BoardException)
            and item.code.error == BoardErrorCode.FORBIDDEN.code.error
            for item in results
        )
        == 1
    )
    result = next(item for item in results if not isinstance(item, Exception))
    assert result.owner_id == target_id and result.board_revision == before.board.revision + 1
    async with test_db() as db:
        assert (await db.get(BoardMember, (board_id, owner_id))).role == "admin"
        assert (await db.get(BoardMember, (board_id, target_id))).role == "owner"
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMember)
                .where(BoardMember.board_id == board_id, BoardMember.role == "owner")
            )
            == 1
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMemberAudit)
                .where(
                    BoardMemberAudit.board_id == board_id,
                    BoardMemberAudit.action == "ownership_transferred",
                )
            )
            == 1
        )
        target_email = (await db.get(User, target_id)).email
        with pytest.raises(IntegrityError):
            await db.execute(
                text(
                    "UPDATE board_members SET role='owner' WHERE board_id=:board AND user_id=:user"
                ),
                {"board": board_id, "user": owner_id},
            )
        await db.rollback()
    with pytest.raises(AuthException) as protected:
        await Users.delete_account(target_id, target_email)
    assert protected.value.code.error == AuthErrorCode.BOARD_OWNERSHIP_REQUIRED.code.error
    archived = await service.update(
        target_id,
        board_id,
        BoardSettingsPatchForm(
            expected_revision=result.board_revision, reason="PG 보관", status="archived"
        ),
    )
    delete_form = BoardDeleteForm(
        expected_revision=archived.board_revision, confirm_slug=archived.board.slug
    )
    with pytest.raises(BoardException) as forbidden:
        await service.delete_board(owner_id, board_id, delete_form)
    assert forbidden.value.code.error == BoardErrorCode.FORBIDDEN.code.error
    saved = await service.home(target_id, board_id=board_id)
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=SQLAlchemyError("commit failed")
    ):
        with pytest.raises(BoardException) as rejected:
            await service.delete_board(target_id, board_id, delete_form)
        assert rejected.value.code.error == BoardErrorCode.UNAVAILABLE.code.error
    assert await service.home(target_id, board_id=board_id) == saved
    await service.delete_board(target_id, board_id, delete_form)
    async with test_db() as db:
        assert await db.get(Board, board_id) is None
        assert (
            await db.scalar(
                select(func.count())
                .select_from(BoardMember)
                .where(BoardMember.board_id == board_id)
            )
            == 0
        )
        assert await db.get(User, target_id) is not None


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

        monkeypatch.setattr("app.models.board.get_db", test_db)
        monkeypatch.setattr("app.models.user.get_db", test_db)
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
            service = BoardService(BoardPermissionService(), BoardRepository())
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
            async with test_db() as db:
                newcomer = User(
                    email="pg-join@example.com",
                    name="Joiner",
                    role="user",
                    is_active=True,
                    is_verified=True,
                )
                db.add(newcomer)
                await db.commit()
                newcomer_id = newcomer.id
            membership = BoardMembershipService(BoardPermissionService(), BoardRepository())
            joined = await asyncio.gather(
                membership.join(newcomer_id, board.id), membership.join(newcomer_id, board.id)
            )
            assert joined[0] == joined[1] and joined[0].role == "member"
            async with test_db() as db:
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(BoardMemberAudit)
                        .where(
                            BoardMemberAudit.board_id == board.id,
                            BoardMemberAudit.action == "member_joined",
                        )
                    )
                    == 1
                )
                assert (await db.get(Board, board.id)).revision == 1
            updates = await asyncio.gather(
                membership.change_member(
                    user_id,
                    board.id,
                    newcomer_id,
                    BoardMemberPatchForm(
                        expected_revision=1, reason="동시 제재", status="suspended"
                    ),
                ),
                membership.change_member(
                    user_id,
                    board.id,
                    newcomer_id,
                    BoardMemberPatchForm(expected_revision=1, reason="동시 역할", role="moderator"),
                ),
                return_exceptions=True,
            )
            assert sum(not isinstance(item, Exception) for item in updates) == 1
            assert (
                sum(
                    isinstance(item, BoardException)
                    and item.code.error == BoardErrorCode.CONFLICT.code.error
                    for item in updates
                )
                == 1
            )
            async with test_db() as db:
                assert (await db.get(Board, board.id)).revision == 2
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(BoardMemberAudit)
                        .where(
                            BoardMemberAudit.board_id == board.id,
                            BoardMemberAudit.action == "member_updated",
                        )
                    )
                    == 1
                )
                assert (
                    await db.scalar(
                        text(
                            "SELECT count(*) FROM pg_indexes WHERE schemaname=:schema AND indexname IN ('ix_board_members_page','ix_board_member_audit_page')"
                        ),
                        {"schema": schema},
                    )
                    == 2
                )
            restored = await membership.change_member(
                user_id,
                board.id,
                newcomer_id,
                BoardMemberPatchForm(
                    expected_revision=2, reason="복원", role="member", status="active"
                ),
            )
            assert restored.board_revision == 3
            with pytest.raises(BoardException) as rejected:
                await membership.change_member(
                    user_id,
                    board.id,
                    newcomer_id,
                    BoardMemberPatchForm(
                        expected_revision=3,
                        reason="다른 보드 등급",
                        grade_id=other_grade,
                        status="banned",
                    ),
                )
            assert rejected.value.code.error == BoardErrorCode.INVALID_GRADE.code.error
            async with test_db() as db:
                assert (await db.get(BoardMember, (board.id, newcomer_id))).status == "active"
                assert (await db.get(Board, board.id)).revision == 3
            await assert_grade_management(test_db, user_id, board.id)
            await assert_member_invitations(test_db, user_id, board.id)
            await assert_board_settings(test_db, user_id, board.id, newcomer_id)
            await assert_board_lifecycle(test_db, user_id, board.id, newcomer_id)
            await service.delete_board(
                user_id,
                other.id,
                BoardDeleteForm(expected_revision=0, confirm_slug=other.slug),
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
