"""Board creation is one aggregate transaction; reads always evaluate current membership."""

import base64
import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, or_, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.error import AuthErrorCode, AuthException
from app.core.error.board_exception import BoardErrorCode, BoardException
from app.models.board import (
    Board,
    BoardAction,
    BoardCreateForm,
    BoardDeleteForm,
    BoardHomeResponse,
    BoardInterest,
    BoardLayout,
    BoardMember,
    BoardMemberAudit,
    BoardMemberGrade,
    BoardPageResponse,
    BoardPolicy,
    BoardSummary,
    GradeSummary,
    MembershipSummary,
    Shelf,
    ShelfPolicy,
    ShelfSummary,
)
from app.models.interest import Interest
from app.models.user import User

ACTIONS: tuple[BoardAction, ...] = ("read_canvas", "create_canvas", "create_comment", "react")
STAFF = {"owner", "admin", "moderator"}


class BoardService:
    async def create(self, user_id: int, form: BoardCreateForm) -> BoardSummary:
        try:
            async with get_db() as db:
                if db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                creator = await db.scalar(
                    select(User.id)
                    .where(User.id == user_id, User.is_active.is_(True))
                    .with_for_update()
                )
                if creator is None:
                    raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
                count = await db.scalar(
                    select(func.count()).select_from(Board).where(Board.owner_id == user_id)
                )
                if count >= 20:
                    raise BoardException(BoardErrorCode.LIMIT_REACHED)
                if await db.scalar(select(Board.id).where(Board.slug == form.slug)):
                    raise BoardException(BoardErrorCode.SLUG_TAKEN)
                interests = list(
                    (
                        await db.scalars(
                            select(Interest).where(
                                Interest.slug.in_(form.interest_ids), Interest.active.is_(True)
                            )
                        )
                    ).all()
                )
                by_slug = {item.slug: item for item in interests}
                if len(by_slug) != len(form.interest_ids):
                    raise BoardException(BoardErrorCode.INVALID_INTEREST)
                board = Board(
                    owner_id=user_id,
                    name=form.name,
                    slug=form.slug,
                    description=form.description,
                    visibility=form.visibility,
                    join_policy=form.join_policy,
                )
                db.add(board)
                await db.flush()
                await self._initialize(
                    db, board, user_id, [by_slug[key].id for key in form.interest_ids]
                )
                await db.commit()
                return self._summary(board, form.interest_ids)
        except IntegrityError:
            # The unique constraint, rather than the preflight query, arbitrates slug races.
            async with get_db() as db:
                if await db.scalar(select(Board.id).where(Board.slug == form.slug)):
                    raise BoardException(BoardErrorCode.SLUG_TAKEN) from None
            raise BoardException(BoardErrorCode.UNAVAILABLE) from None
        except SQLAlchemyError as error:
            raise BoardException(BoardErrorCode.UNAVAILABLE) from error

    async def _initialize(
        self, db: AsyncSession, board: Board, user_id: int, interest_ids: list[int]
    ) -> None:
        grades = [
            BoardMemberGrade(board_id=board.id, name=name, rank=rank, is_default=rank == 0)
            for name, rank in (("뉴커머", 0), ("피너", 10), ("큐레이터", 20))
        ]
        db.add_all(grades)
        await db.flush()
        db.add(
            BoardMember(
                board_id=board.id,
                user_id=user_id,
                role="owner",
                status="active",
                grade_id=grades[0].id,
            )
        )
        for action in ACTIONS:
            public_read = action == "read_canvas" and board.visibility == "public"
            db.add(
                BoardPolicy(
                    board_id=board.id,
                    action=action,
                    audience="public" if public_read else "members",
                    min_grade_id=None
                    if public_read
                    else grades[1 if action == "create_canvas" else 0].id,
                    staff_only=False,
                    staff_bypass=True,
                )
            )
        db.add_all(
            [
                BoardInterest(board_id=board.id, interest_id=interest, position=index)
                for index, interest in enumerate(interest_ids)
            ]
        )
        shelves = [
            Shelf(
                board_id=board.id,
                name="공지사항",
                slug="notice",
                purpose="notice",
                sort_order=0,
                icon="megaphone",
                is_default=False,
            ),
            Shelf(
                board_id=board.id,
                name="자유 이야기",
                slug="general",
                purpose="general",
                sort_order=1,
                is_default=True,
            ),
        ]
        db.add_all(shelves)
        await db.flush()
        for action in ("create_canvas", "create_comment"):
            db.add(
                ShelfPolicy(
                    board_id=board.id,
                    shelf_id=shelves[0].id,
                    action=action,
                    audience="members",
                    min_grade_id=None,
                    staff_only=True,
                    staff_bypass=False,
                )
            )
        db.add(
            BoardLayout(
                board_id=board.id,
                document={
                    "schema_version": 1,
                    "widgets": [
                        {
                            "id": "board-intro",
                            "type": "board_intro",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 600, "height": 240},
                        },
                        {
                            "id": "shelves",
                            "type": "shelf_navigation",
                            "position": {"x": 100, "y": 420},
                            "size": {"width": 600, "height": 300},
                        },
                        {
                            "id": "latest",
                            "type": "canvas_collection",
                            "source": {"board_id": str(board.id), "sort": "latest", "limit": 6},
                            "position": {"x": 850, "y": 100},
                            "size": {"width": 850, "height": 650},
                        },
                    ],
                },
            )
        )
        db.add(
            BoardMemberAudit(
                board_id=board.id,
                actor_user_id=user_id,
                target_user_id=user_id,
                action="board_created",
                changes={"role": "owner", "grade_id": str(grades[0].id)},
            )
        )
        await db.flush()

    @staticmethod
    def _summary(board: Board, interests: list[str]) -> BoardSummary:
        created = board.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return BoardSummary(
            id=board.id,
            owner_id=board.owner_id,
            slug=board.slug,
            name=board.name,
            description=board.description,
            visibility=board.visibility,
            join_policy=board.join_policy,
            status=board.status,
            revision=board.revision,
            interest_ids=interests,
            created_at=created,
        )

    async def list(
        self,
        user_id: int | None,
        *,
        limit: int,
        cursor: str | None,
        q: str,
        interest_id: str | None,
        mine: bool,
    ) -> BoardPageResponse:
        if mine and user_id is None:
            raise AuthException(code=AuthErrorCode.INVALID_TOKEN)
        fingerprint = hashlib.sha256(
            json.dumps([q, interest_id, mine], ensure_ascii=False).encode()
        ).hexdigest()
        clause = Board.visibility == "public"
        if user_id is not None:
            active_member = exists().where(
                BoardMember.board_id == Board.id,
                BoardMember.user_id == user_id,
                BoardMember.status == "active",
            )
            blocked_member = exists().where(
                BoardMember.board_id == Board.id,
                BoardMember.user_id == user_id,
                BoardMember.status.in_(["banned", "suspended"]),
            )
            clause = and_(or_(clause, active_member), ~blocked_member)
        query = select(Board).where(Board.status.in_(["active", "archived"]), clause)
        if mine:
            query = query.where(Board.owner_id == user_id)
        if q:
            query = query.where(Board.name.contains(q, autoescape=True))
        if interest_id:
            query = query.where(
                exists().where(
                    BoardInterest.board_id == Board.id,
                    BoardInterest.interest_id == Interest.id,
                    Interest.slug == interest_id,
                    Interest.active.is_(True),
                )
            )
        if cursor:
            try:
                decoded = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                created = datetime.fromisoformat(decoded["created_at"])
                last_id = UUID(decoded["id"])
                if (
                    created.tzinfo is None
                    or decoded["filter"] != fingerprint
                    or decoded["version"] != 1
                ):
                    raise ValueError("Cursor does not match the query.")
            except (ValueError, KeyError, TypeError, UnicodeError):
                raise BoardException(BoardErrorCode.INVALID_CURSOR) from None
            query = query.where(
                or_(
                    Board.created_at < created,
                    and_(Board.created_at == created, Board.id < last_id),
                )
            )
        async with get_db() as db:
            boards = list(
                (
                    await db.scalars(
                        query.order_by(Board.created_at.desc(), Board.id.desc()).limit(limit + 1)
                    )
                ).all()
            )
            selected = boards[:limit]
            interests = {board.id: [] for board in selected}
            for board_id, slug in (
                await db.execute(
                    select(BoardInterest.board_id, Interest.slug)
                    .join(Interest, Interest.id == BoardInterest.interest_id)
                    .where(BoardInterest.board_id.in_(interests), Interest.active.is_(True))
                    .order_by(BoardInterest.position)
                )
            ).all():
                interests[board_id].append(slug)
            items = [self._summary(board, interests[board.id]) for board in selected]
        next_cursor = None
        if len(boards) > limit:
            last = items[-1]
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "version": 1,
                            "created_at": last.created_at.isoformat(),
                            "id": str(last.id),
                            "filter": fingerprint,
                        }
                    ).encode()
                )
                .decode()
                .rstrip("=")
            )
        return BoardPageResponse(items=items, next_cursor=next_cursor)

    async def home(
        self, user_id: int | None, *, board_id: UUID | None = None, slug: str | None = None
    ) -> BoardHomeResponse:
        async with get_db() as db:
            board = await db.scalar(
                select(Board).where(
                    Board.id == board_id if board_id is not None else Board.slug == slug
                )
            )
            if board is None or board.status == "suspended":
                raise BoardException(BoardErrorCode.NOT_FOUND)
            member = await db.get(BoardMember, (board.id, user_id)) if user_id is not None else None
            self._check_read(board, member)
            grades = list(
                (
                    await db.scalars(
                        select(BoardMemberGrade)
                        .where(BoardMemberGrade.board_id == board.id)
                        .order_by(BoardMemberGrade.rank)
                    )
                ).all()
            )
            by_id = {grade.id: grade for grade in grades}
            policies = {
                (policy.action): policy
                for policy in (
                    await db.scalars(select(BoardPolicy).where(BoardPolicy.board_id == board.id))
                ).all()
            }
            overrides = {
                (policy.shelf_id, policy.action): policy
                for policy in (
                    await db.scalars(select(ShelfPolicy).where(ShelfPolicy.board_id == board.id))
                ).all()
            }
            shelves = []
            for shelf in (
                await db.scalars(
                    select(Shelf)
                    .where(Shelf.board_id == board.id, Shelf.is_visible.is_(True))
                    .order_by(Shelf.sort_order, Shelf.id)
                )
            ).all():
                capabilities = {
                    action: self._allowed(
                        board,
                        member,
                        overrides.get((shelf.id, action), policies.get(action)),
                        by_id,
                        action,
                    )
                    for action in ACTIONS
                }
                if capabilities["read_canvas"]:
                    shelves.append(
                        ShelfSummary(
                            id=shelf.id,
                            slug=shelf.slug,
                            name=shelf.name,
                            description=shelf.description,
                            icon=shelf.icon,
                            purpose=shelf.purpose,
                            classification=shelf.classification,
                            sort_order=shelf.sort_order,
                            is_default=shelf.is_default,
                            capabilities=capabilities,
                        )
                    )
            interests = list(
                (
                    await db.scalars(
                        select(Interest.slug)
                        .join(BoardInterest, BoardInterest.interest_id == Interest.id)
                        .where(BoardInterest.board_id == board.id, Interest.active.is_(True))
                        .order_by(BoardInterest.position)
                    )
                ).all()
            )
            layout = await db.get(BoardLayout, board.id)
            if layout is None:
                raise BoardException(BoardErrorCode.UNAVAILABLE)
            membership = (
                MembershipSummary(
                    role=member.role,
                    status=member.status,
                    grade_id=member.grade_id,
                    grade_name=by_id[member.grade_id].name,
                )
                if member
                else None
            )
            return BoardHomeResponse(
                board=self._summary(board, interests),
                rules=board.rules,
                membership=membership,
                grades=[
                    GradeSummary(id=g.id, name=g.name, rank=g.rank, is_default=g.is_default)
                    for g in grades
                ],
                shelves=shelves,
                layout=layout.document,
                layout_revision=layout.revision,
            )

    @staticmethod
    def _check_read(board: Board, member: BoardMember | None) -> None:
        if member and member.status in {"suspended", "banned"}:
            raise BoardException(BoardErrorCode.NOT_FOUND)
        if board.visibility == "private" and (member is None or member.status != "active"):
            raise BoardException(BoardErrorCode.NOT_FOUND)

    @staticmethod
    def _allowed(
        board: Board,
        member: BoardMember | None,
        policy: BoardPolicy | ShelfPolicy | None,
        grades: dict[UUID, BoardMemberGrade],
        action: str,
    ) -> bool:
        if policy is None or (action != "read_canvas" and board.status != "active"):
            return False
        if policy.audience == "public" and action == "read_canvas" and board.visibility == "public":
            return True
        if member is None or member.status != "active":
            return False
        staff = member.role in STAFF
        if policy.staff_only:
            return staff
        if staff and policy.staff_bypass:
            return True
        own = grades.get(member.grade_id)
        minimum = grades.get(policy.min_grade_id)
        return own is not None and minimum is not None and own.rank >= minimum.rank

    async def delete_empty(self, user_id: int, board_id: UUID, form: BoardDeleteForm) -> None:
        try:
            async with get_db() as db:
                if db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                board = await db.scalar(select(Board).where(Board.id == board_id).with_for_update())
                if board is None:
                    raise BoardException(BoardErrorCode.NOT_FOUND)
                member = await db.get(BoardMember, (board_id, user_id))
                self._check_read(board, member)
                if (
                    board.owner_id != user_id
                    or member is None
                    or member.role != "owner"
                    or member.status != "active"
                    or board.status == "suspended"
                ):
                    raise BoardException(BoardErrorCode.FORBIDDEN)
                if board.revision != form.expected_revision:
                    raise BoardException(
                        BoardErrorCode.CONFLICT, {"current_revision": board.revision}
                    )
                if board.slug != form.confirm_slug:
                    raise BoardException(BoardErrorCode.DELETE_CONFIRMATION)
                if (
                    await db.scalar(
                        select(func.count())
                        .select_from(BoardMember)
                        .where(BoardMember.board_id == board_id)
                    )
                    != 1
                ):
                    raise BoardException(BoardErrorCode.NOT_EMPTY)
                # Explicit child order also works with SQLite's immediate FK checks.
                # Future Canvas/Asset restrictive FKs make nonempty deletion fail closed.
                for model in (
                    ShelfPolicy,
                    BoardPolicy,
                    BoardMemberAudit,
                    BoardInterest,
                    BoardLayout,
                    BoardMember,
                    Shelf,
                    BoardMemberGrade,
                ):
                    await db.execute(delete(model).where(model.board_id == board_id))
                await db.delete(board)
                await db.commit()
        except IntegrityError:
            raise BoardException(BoardErrorCode.NOT_EMPTY) from None
        except SQLAlchemyError as error:
            raise BoardException(BoardErrorCode.UNAVAILABLE) from error
