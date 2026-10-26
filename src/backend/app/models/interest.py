from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import Boolean, ForeignKey, Integer, String, select, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.db.session import Base, get_db


class Interest(Base):
    __tablename__ = "interests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name_ko: Mapped[str] = mapped_column(String(40), nullable=False)
    name_en: Mapped[str] = mapped_column(String(40), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=1000, server_default=text("1000"), nullable=False
    )
    aliases: Mapped[list["InterestAlias"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class InterestAlias(Base):
    __tablename__ = "interest_aliases"
    alias: Mapped[str] = mapped_column(String(80), primary_key=True)
    interest_id: Mapped[int] = mapped_column(
        ForeignKey("interests.id", ondelete="CASCADE"), nullable=False
    )


class UserInterest(Base):
    __tablename__ = "user_interests"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    interest_id: Mapped[int] = mapped_column(
        ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    interest: Mapped[Interest] = relationship(lazy="joined")


class InterestResponse(BaseModel):
    id: str
    name_ko: str
    name_en: str
    aliases: list[str] = Field(default_factory=list)


class InterestCatalogResponse(BaseModel):
    items: list[InterestResponse]


class InterestCreateForm(BaseModel):
    sort_order: int = Field(default=1000, ge=0, le=10000)
    id: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name_ko: str = Field(min_length=1, max_length=40)
    name_en: str = Field(min_length=1, max_length=40)
    aliases: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("name_ko", "name_en")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be blank.")
        return value.strip()

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 80 for item in value):
            raise ValueError("Aliases must contain 1-80 characters.")
        return list(dict.fromkeys(item.strip().casefold() for item in value))


class InterestUpdateForm(BaseModel):
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    name_ko: str | None = Field(default=None, min_length=1, max_length=40)
    name_en: str | None = Field(default=None, min_length=1, max_length=40)
    aliases: list[str] | None = Field(default=None, max_length=20)
    active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("Provide non-null fields to update.")
        if self.name_ko is not None:
            self.name_ko = InterestCreateForm.strip_name(self.name_ko)
        if self.name_en is not None:
            self.name_en = InterestCreateForm.strip_name(self.name_en)
        if self.aliases is not None:
            self.aliases = InterestCreateForm.validate_aliases(self.aliases)
        return self


class InterestAdminResponse(InterestResponse):
    sort_order: int = 1000
    active: bool


class InterestRepository:
    async def list_active(self) -> InterestCatalogResponse:
        async with get_db() as db:
            items = (
                await db.scalars(
                    select(Interest)
                    .where(Interest.active.is_(True))
                    .options(selectinload(Interest.aliases))
                    .order_by(Interest.sort_order, Interest.id)
                )
            ).all()
            return InterestCatalogResponse(
                items=[
                    InterestResponse(
                        id=item.slug,
                        name_ko=item.name_ko,
                        name_en=item.name_en,
                        aliases=[alias.alias for alias in item.aliases],
                    )
                    for item in items
                ]
            )

    async def create(self, form: InterestCreateForm) -> InterestAdminResponse:
        async with get_db() as db:
            item = Interest(
                slug=form.id,
                name_ko=form.name_ko,
                name_en=form.name_en,
                active=True,
                sort_order=form.sort_order,
            )
            terms = list(
                dict.fromkeys(
                    [form.id, form.name_ko.casefold(), form.name_en.casefold(), *form.aliases]
                )
            )
            item.aliases = [InterestAlias(alias=term) for term in terms]
            db.add(item)
            await db.commit()
            return InterestAdminResponse(
                id=item.slug,
                name_ko=item.name_ko,
                name_en=item.name_en,
                active=item.active,
                sort_order=item.sort_order,
                aliases=terms,
            )

    async def update(self, slug: str, form: InterestUpdateForm) -> InterestAdminResponse | None:
        async with get_db() as db:
            item = await db.scalar(
                select(Interest)
                .where(Interest.slug == slug)
                .options(selectinload(Interest.aliases))
            )
            if item is None:
                return None
            for field in ("name_ko", "name_en", "active", "sort_order"):
                if field in form.model_fields_set:
                    setattr(item, field, getattr(form, field))
            terms = list(
                dict.fromkeys(
                    [
                        *([item.name_ko.casefold()] if "name_ko" in form.model_fields_set else []),
                        *([item.name_en.casefold()] if "name_en" in form.model_fields_set else []),
                        *(
                            form.aliases
                            if form.aliases is not None
                            else [alias.alias for alias in item.aliases]
                        ),
                    ]
                )
            )
            existing = {alias.alias: alias for alias in item.aliases}
            item.aliases = [existing.get(term) or InterestAlias(alias=term) for term in terms]
            await db.commit()
            return InterestAdminResponse(
                id=item.slug,
                name_ko=item.name_ko,
                name_en=item.name_en,
                active=item.active,
                sort_order=item.sort_order,
                aliases=terms,
            )

    async def list_admin(self) -> list[InterestAdminResponse]:
        async with get_db() as db:
            items = (
                await db.scalars(
                    select(Interest)
                    .options(selectinload(Interest.aliases))
                    .order_by(Interest.sort_order, Interest.id)
                )
            ).all()
            return [
                InterestAdminResponse(
                    id=item.slug,
                    name_ko=item.name_ko,
                    name_en=item.name_en,
                    active=item.active,
                    sort_order=item.sort_order,
                    aliases=[alias.alias for alias in item.aliases],
                )
                for item in items
            ]
