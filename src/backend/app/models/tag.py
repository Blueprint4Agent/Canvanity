"""Public free-tag dictionary and same-session Canvas links; persistence stays here."""

import unicodedata
from dataclasses import dataclass
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Uuid, delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.auth_exception import AuthErrorCode, AuthException
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.core.error.tag_exception import TagErrorCode, TagException
from app.models.user import User

MAX_CANVAS_TAGS = 10


def normalize_tag_name(value: str, *, allow_empty: bool = False) -> tuple[str, str]:
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise ValueError("Tag names must contain valid UTF-8.") from error
    if any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in value):
        raise ValueError("Tag names cannot contain control or format characters.")
    name = unicodedata.normalize("NFC", value).strip()
    key = unicodedata.normalize("NFC", name.casefold())
    if (not name and not allow_empty) or len(name) > 40 or len(key) > 80:
        raise ValueError("Tag names must contain 1-40 characters and a normalized key up to 80.")
    return name, key


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        CheckConstraint("length(name) BETWEEN 1 AND 40", name="ck_tag_name_length"),
        CheckConstraint(
            "length(normalized_name) BETWEEN 1 AND 80", name="ck_tag_normalized_name_length"
        ),
        Index("uq_tag_normalized_name", "normalized_name", unique=True),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(40))
    normalized_name: Mapped[str] = mapped_column(
        String(80).with_variant(String(80, collation="C"), "postgresql")
    )


class CanvasTag(Base):
    __tablename__ = "canvas_tags"
    __table_args__ = (Index("ix_canvas_tags_tag", "tag_id"),)
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True
    )


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class TagCatalogResponse(BaseModel):
    items: list[TagResponse]


class TagCreateForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=40)

    @field_validator("name", mode="before")
    @classmethod
    def normalized_display_name(cls, value: object) -> object:
        return normalize_tag_name(value)[0] if isinstance(value, str) else value


class TagSearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=40)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("q", mode="before")
    @classmethod
    def normalized_query(cls, value: object) -> object:
        return normalize_tag_name(value, allow_empty=True)[0] if isinstance(value, str) else value


@dataclass(frozen=True)
class TagCreationResult:
    tag: TagResponse
    created: bool


class TagTransaction:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def canvas_tags(self, canvas_id: UUID) -> list[TagResponse]:
        rows = (
            await self._db.scalars(
                select(Tag)
                .join(CanvasTag, CanvasTag.tag_id == Tag.id)
                .where(CanvasTag.canvas_id == canvas_id)
                .order_by(Tag.normalized_name, Tag.id)
            )
        ).all()
        return [TagResponse.model_validate(row) for row in rows]

    async def replace_canvas_tags(self, canvas_id: UUID, tag_ids: list[UUID]) -> bool:
        requested = set(tag_ids)
        if requested:
            found = set(
                (
                    await self._db.scalars(
                        select(Tag.id)
                        .where(Tag.id.in_(requested))
                        .order_by(Tag.id)
                        .with_for_update(read=True)
                    )
                ).all()
            )
            if found != requested:
                raise CanvasException(CanvasErrorCode.INVALID_TAGS)
        existing = set(
            (
                await self._db.scalars(
                    select(CanvasTag.tag_id).where(CanvasTag.canvas_id == canvas_id)
                )
            ).all()
        )
        if existing == requested:
            return False
        await self._db.execute(delete(CanvasTag).where(CanvasTag.canvas_id == canvas_id))
        self._db.add_all(CanvasTag(canvas_id=canvas_id, tag_id=tag_id) for tag_id in requested)
        await self._db.flush()
        return True


class TagRepository:
    async def search(self, query: TagSearchQuery) -> TagCatalogResponse:
        _, key = normalize_tag_name(query.q, allow_empty=True)
        try:
            async with get_db() as db:
                rows = (
                    await db.scalars(
                        select(Tag)
                        .where(Tag.normalized_name.contains(key, autoescape=True))
                        .order_by(Tag.normalized_name, Tag.id)
                        .limit(query.limit)
                    )
                ).all()
                return TagCatalogResponse(items=[TagResponse.model_validate(row) for row in rows])
        except SQLAlchemyError as error:
            raise TagException(TagErrorCode.UNAVAILABLE) from error

    async def get_or_create(self, user_id: int, form: TagCreateForm) -> TagCreationResult:
        name, key = normalize_tag_name(form.name)
        try:
            async with get_db() as db:
                if db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE"))
                active = await db.scalar(
                    select(User.id)
                    .where(User.id == user_id, User.is_active.is_(True))
                    .with_for_update(read=True)
                )
                if active is None:
                    raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
                insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
                new_id = await db.scalar(
                    insert(Tag)
                    .values(id=uuid4(), name=name, normalized_name=key)
                    .on_conflict_do_nothing(index_elements=[Tag.normalized_name])
                    .returning(Tag.id)
                )
                tag = await db.scalar(select(Tag).where(Tag.normalized_name == key))
                if tag is None:
                    raise TagException(TagErrorCode.UNAVAILABLE)
                result = TagCreationResult(
                    TagResponse.model_validate(tag), created=new_id is not None
                )
                await db.commit()
                return result
        except SQLAlchemyError as error:
            raise TagException(TagErrorCode.UNAVAILABLE) from error
