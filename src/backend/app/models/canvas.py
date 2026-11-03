"""Canvas entities, API schemas and persistence; sessions never leave this module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticSerializationError
from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    delete,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db
from app.core.error.canvas_exception import CanvasErrorCode, CanvasException
from app.models.board import BoardTransaction, Shelf
from app.models.tag import MAX_CANVAS_TAGS, TagResponse, TagTransaction
from app.utils.canvas_limits import MAX_CANVAS_DOCUMENT_BYTES

MAX_CANVAS_REVISION = 2**63 - 1
CANVAS_TRASH_RETENTION_DAYS = 30
CANVAS_FIELDS = ("title", "summary", "shelf_id", "visibility")
CANVAS_PATCH_FIELDS = (*CANVAS_FIELDS, "tag_ids")
CanvasStatus = Literal["draft", "trashed"]
CanvasVisibility = Literal["public", "members"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class Canvas(Base):
    __tablename__ = "canvases"
    __table_args__ = (
        Index("uq_canvas_board_id", "board_id", "id", unique=True),
        ForeignKeyConstraint(
            ["board_id", "shelf_id"],
            ["shelves.board_id", "shelves.id"],
            ondelete="RESTRICT",
            name="fk_canvas_shelf",
        ),
        CheckConstraint("status IN ('draft','trashed')", name="ck_canvas_status"),
        CheckConstraint("visibility IN ('public','members')", name="ck_canvas_visibility"),
        CheckConstraint("revision >= 0", name="ck_canvas_revision"),
        CheckConstraint(
            "(status = 'draft' AND trashed_at IS NULL) OR (status = 'trashed' AND trashed_at IS NOT NULL)",
            name="ck_canvas_trash_state",
        ),
        Index("ix_canvases_board_shelf", "board_id", "shelf_id"),
        Index("ix_canvases_author_id", "author_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="RESTRICT"))
    shelf_id: Mapped[UUID] = mapped_column(Uuid)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500), default="", server_default="")
    status: Mapped[str] = mapped_column(String(12), default="draft", server_default="draft")
    visibility: Mapped[str] = mapped_column(String(10), default="members", server_default="members")
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanvasDocument(Base):
    __tablename__ = "canvas_documents"
    __table_args__ = (CheckConstraint("revision >= 0", name="ck_canvas_document_revision"),)
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    document: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanvasPublicationCounter(Base):
    """Persistent state CAS token, including transitions to an unpublished state."""

    __tablename__ = "canvas_publication_counters"
    __table_args__ = (CheckConstraint("revision >= 0", name="ck_publication_counter_revision"),)
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    revision: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")


class CanvasPublication(Base):
    __tablename__ = "canvas_publications"
    __table_args__ = (
        CheckConstraint("publication_revision > 0", name="ck_publication_revision"),
        CheckConstraint(
            "source_metadata_revision >= 0 AND source_document_revision >= 0",
            name="ck_publication_source_revisions",
        ),
        CheckConstraint("visibility IN ('public','members')", name="ck_publication_visibility"),
        Index("ix_canvas_publications_published", "published_at", "canvas_id"),
    )
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), primary_key=True
    )
    publication_revision: Mapped[int] = mapped_column(BigInteger)
    source_metadata_revision: Mapped[int] = mapped_column(BigInteger)
    source_document_revision: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    visibility: Mapped[str] = mapped_column(String(10))
    document: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CanvasPublicationTag(Base):
    __tablename__ = "canvas_publication_tags"
    __table_args__ = (
        CheckConstraint("position >= 0 AND position < 10", name="ck_publication_tag_position"),
        UniqueConstraint("canvas_id", "position", name="uq_publication_tag_position"),
        Index("ix_publication_tags_tag", "tag_id", "canvas_id"),
    )
    canvas_id: Mapped[UUID] = mapped_column(
        ForeignKey("canvas_publications.canvas_id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)


MAX_CANVAS_ELEMENTS = 2_000
MAX_CANVAS_TEXT_LENGTH = 20_000
MAX_CANVAS_POINTS = 20_000
MAX_CANVAS_COORDINATE = 100_000
MAX_SAFE_JSON_INTEGER = 2**53 - 1
CANVAS_FONT_FAMILIES = (1, 2, 3, 5, 6, 7, 8, 9)

CanvasElementId = Annotated[str, Field(min_length=1, max_length=80)]
CanvasCoordinate = Annotated[float, Field(ge=-MAX_CANVAS_COORDINATE, le=MAX_CANVAS_COORDINATE)]
CanvasLength = Annotated[float, Field(ge=0, le=MAX_CANVAS_COORDINATE)]
CanvasPositiveLength = Annotated[float, Field(gt=0, le=MAX_CANVAS_COORDINATE)]
CanvasPoint = Annotated[list[CanvasCoordinate], Field(min_length=2, max_length=2)]
CanvasColor = Annotated[
    str, Field(pattern=r"^(#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{8}|transparent)$")
]
CanvasImageFlip = Annotated[int, Field(json_schema_extra={"enum": [-1, 1]})]


def _version_one(value: object) -> int:
    if type(value) is not int or value != 1:
        raise ValueError("Only integer version 1 is supported.")
    return value


def _false_only(value: object) -> bool:
    if value is not False:
        raise ValueError("Only boolean false is supported.")
    return value


CanvasVersionOne = Annotated[Literal[1], BeforeValidator(_version_one)]
CanvasFalse = Annotated[Literal[False], BeforeValidator(_false_only)]


class CanvasSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class CanvasEngine(CanvasSchema):
    name: Literal["excalidraw"] = "excalidraw"
    version: Literal["0.18.1"] = "0.18.1"
    adapter_version: CanvasVersionOne = 1


class CanvasSettings(CanvasSchema):
    background: CanvasColor = "#F8F7F4"
    grid: Literal["none", "dots"] = "dots"
    width: int = Field(default=3200, gt=0, le=MAX_CANVAS_COORDINATE)
    height: int = Field(default=2100, gt=0, le=MAX_CANVAS_COORDINATE)


class CanvasPosition(CanvasSchema):
    x: CanvasCoordinate
    y: CanvasCoordinate


class CanvasSize(CanvasSchema):
    width: CanvasLength
    height: CanvasLength


class CanvasEngineRoundness(CanvasSchema):
    type: int = Field(ge=1, le=3)
    value: CanvasLength | None = Field(default=None, exclude_if=lambda value: value is None)


class CanvasEngineBoundElement(CanvasSchema):
    id: CanvasElementId
    type: Literal["arrow", "text"]


class CanvasEngineElement(CanvasSchema):
    """Pinned engine field names are preserved inside engine_element only."""

    id: CanvasElementId
    type: str
    x: CanvasCoordinate
    y: CanvasCoordinate
    width: CanvasLength
    height: CanvasLength
    angle: CanvasCoordinate
    strokeColor: CanvasColor
    backgroundColor: CanvasColor
    fillStyle: Literal["hachure", "cross-hatch", "solid", "zigzag"]
    strokeWidth: float = Field(ge=0, le=1_000)
    strokeStyle: Literal["solid", "dashed", "dotted"]
    roundness: CanvasEngineRoundness | None
    roughness: float = Field(ge=0, le=10)
    opacity: float = Field(ge=0, le=100)
    seed: int = Field(ge=0, le=2**31 - 1)
    version: int = Field(ge=1, le=MAX_SAFE_JSON_INTEGER)
    versionNonce: int = Field(ge=0, le=2**31 - 1)
    index: Annotated[str, Field(min_length=1, max_length=128)] | None
    isDeleted: CanvasFalse
    groupIds: list[CanvasElementId] = Field(max_length=0)
    frameId: None
    boundElements: (
        Annotated[list[CanvasEngineBoundElement], Field(max_length=MAX_CANVAS_ELEMENTS)] | None
    )
    updated: int = Field(ge=0, le=MAX_SAFE_JSON_INTEGER)
    locked: bool


class CanvasEngineText(CanvasEngineElement):
    type: Literal["text"]
    text: str = Field(max_length=MAX_CANVAS_TEXT_LENGTH)
    originalText: str = Field(max_length=MAX_CANVAS_TEXT_LENGTH)
    fontSize: float = Field(gt=0, le=10_000)
    fontFamily: int = Field(json_schema_extra={"enum": list(CANVAS_FONT_FAMILIES)})
    textAlign: Literal["left", "center", "right"]
    verticalAlign: Literal["top", "middle", "bottom"]
    containerId: CanvasElementId | None
    autoResize: bool
    lineHeight: float = Field(gt=0, le=10)

    @field_validator("fontFamily")
    @classmethod
    def supported_font(cls, value: int) -> int:
        if value not in CANVAS_FONT_FAMILIES:
            raise ValueError("Unsupported pinned engine font family.")
        return value


class CanvasEngineShape(CanvasEngineElement):
    type: Literal["rectangle", "ellipse", "diamond"]


class CanvasImageCrop(CanvasSchema):
    x: CanvasLength
    y: CanvasLength
    width: CanvasPositiveLength
    height: CanvasPositiveLength
    naturalWidth: CanvasPositiveLength
    naturalHeight: CanvasPositiveLength

    @model_validator(mode="after")
    def crop_bounds(self):
        if self.x + self.width > self.naturalWidth or self.y + self.height > self.naturalHeight:
            raise ValueError("Image crop must fit within its natural dimensions.")
        return self


class CanvasEngineImage(CanvasEngineElement):
    type: Literal["image"]
    status: Literal["saved"]
    scale: list[CanvasImageFlip] = Field(min_length=2, max_length=2)
    crop: CanvasImageCrop | None

    @field_validator("scale")
    @classmethod
    def flip_axes(cls, value: list[int]) -> list[int]:
        if any(axis not in (-1, 1) for axis in value):
            raise ValueError("Image scale must contain only -1 or 1.")
        return value


class CanvasEngineDrawing(CanvasEngineElement):
    type: Literal["freedraw"]
    points: list[CanvasPoint] = Field(min_length=1, max_length=MAX_CANVAS_POINTS)
    pressures: list[Annotated[float, Field(ge=0, le=1)]] = Field(max_length=MAX_CANVAS_POINTS)
    simulatePressure: bool
    lastCommittedPoint: None

    @model_validator(mode="after")
    def pressure_points(self):
        if len(self.pressures) != len(self.points) and not (
            self.simulatePressure and not self.pressures
        ):
            raise ValueError("Drawing pressures must match points or be empty when simulated.")
        return self


class CanvasEnginePointBinding(CanvasSchema):
    elementId: CanvasElementId
    focus: float = Field(ge=-1, le=1)
    gap: CanvasLength


CanvasArrowhead = Literal[
    "arrow",
    "bar",
    "dot",
    "circle",
    "circle_outline",
    "triangle",
    "triangle_outline",
    "diamond",
    "diamond_outline",
    "crowfoot_one",
    "crowfoot_many",
    "crowfoot_one_or_many",
]


class CanvasEngineLinear(CanvasEngineElement):
    points: list[CanvasPoint] = Field(min_length=2, max_length=MAX_CANVAS_POINTS)
    lastCommittedPoint: None
    startBinding: CanvasEnginePointBinding | None
    endBinding: CanvasEnginePointBinding | None
    startArrowhead: CanvasArrowhead | None
    endArrowhead: CanvasArrowhead | None


class CanvasEngineLine(CanvasEngineLinear):
    type: Literal["line"]

    @model_validator(mode="after")
    def unbound_line(self):
        if self.startBinding is not None or self.endBinding is not None:
            raise ValueError("Only arrows support node bindings in version 1.")
        return self


class CanvasEngineArrow(CanvasEngineLinear):
    type: Literal["arrow"]
    elbowed: CanvasFalse


class CanvasObject(CanvasSchema):
    id: CanvasElementId
    position: CanvasPosition
    size: CanvasSize
    engine_element: CanvasEngineElement

    @model_validator(mode="after")
    def matching_geometry(self):
        element = self.engine_element
        if (self.id, self.position.x, self.position.y, self.size.width, self.size.height) != (
            element.id,
            element.x,
            element.y,
            element.width,
            element.height,
        ):
            raise ValueError("Canonical and engine object identity/geometry must match.")
        if self.size.width == 0 and self.size.height == 0:
            raise ValueError("An object must have a non-zero extent.")
        if isinstance(element, (CanvasEngineText, CanvasEngineShape, CanvasEngineImage)) and (
            self.size.width == 0 or self.size.height == 0
        ):
            raise ValueError("Text, shape and image dimensions must be positive.")
        return self


class CanvasTextNode(CanvasObject):
    type: Literal["text"]
    engine_element: CanvasEngineText


class CanvasShapeNode(CanvasObject):
    type: Literal["shape"]
    engine_element: CanvasEngineShape


class CanvasImageContent(CanvasSchema):
    # JSON/ORM dictionaries carry UUID strings, including model_validate() read paths.
    asset_id: UUID = Field(strict=False)


class CanvasImageNode(CanvasObject):
    type: Literal["image"]
    content: CanvasImageContent
    engine_element: CanvasEngineImage


class CanvasDrawingNode(CanvasObject):
    type: Literal["drawing"]
    engine_element: CanvasEngineDrawing


class CanvasEdge(CanvasObject):
    type: Literal["edge"]
    source_node_id: CanvasElementId | None
    target_node_id: CanvasElementId | None
    engine_element: Annotated[CanvasEngineLine | CanvasEngineArrow, Field(discriminator="type")]


CanvasNode = Annotated[
    CanvasTextNode | CanvasShapeNode | CanvasImageNode | CanvasDrawingNode,
    Field(discriminator="type"),
]


class CanvasContent(CanvasSchema):
    schema_version: CanvasVersionOne = 1
    engine: CanvasEngine = Field(default_factory=CanvasEngine)
    settings: CanvasSettings = Field(default_factory=CanvasSettings)
    nodes: list[CanvasNode] = Field(default_factory=list, max_length=MAX_CANVAS_ELEMENTS)
    edges: list[CanvasEdge] = Field(default_factory=list, max_length=MAX_CANVAS_ELEMENTS)
    element_order: list[CanvasElementId] = Field(
        default_factory=list, max_length=MAX_CANVAS_ELEMENTS
    )

    @model_validator(mode="before")
    @classmethod
    def total_elements(cls, data):
        if isinstance(data, dict):
            nodes, edges = data.get("nodes", []), data.get("edges", [])
            if isinstance(nodes, list) and isinstance(edges, list):
                if len(nodes) + len(edges) > MAX_CANVAS_ELEMENTS:
                    raise ValueError("Canvas document exceeds the total element limit.")
        return data

    @model_validator(mode="after")
    def document_integrity(self):
        objects = [*self.nodes, *self.edges]
        by_id = {item.id: item for item in objects}
        if len(by_id) != len(objects):
            raise ValueError("Canvas object IDs must be unique across nodes and edges.")
        if len(self.element_order) != len(by_id) or set(self.element_order) != set(by_id):
            raise ValueError("Element order must contain every object ID exactly once.")

        for item in objects:
            references = item.engine_element.boundElements or []
            if len({ref.id for ref in references}) != len(references):
                raise ValueError("Bound element references must be unique.")
            if sum(ref.type == "text" for ref in references) > 1:
                raise ValueError("A container can have at most one bound text object.")
            for ref in references:
                target = by_id.get(ref.id)
                if ref.type == "text":
                    if not isinstance(target, CanvasTextNode) or (
                        target.engine_element.containerId != item.id
                    ):
                        raise ValueError("Bound text must refer back to its container.")
                elif not isinstance(target, CanvasEdge) or (
                    target.engine_element.type != "arrow"
                    or item.id not in (target.source_node_id, target.target_node_id)
                ):
                    raise ValueError("Bound arrows must refer back to their node.")

            if isinstance(item, CanvasTextNode) and item.engine_element.containerId is not None:
                container = by_id.get(item.engine_element.containerId)
                if not isinstance(container, CanvasShapeNode) and not (
                    isinstance(container, CanvasEdge) and container.engine_element.type == "arrow"
                ):
                    raise ValueError("Text containers must be a shape or arrow in this document.")
                if not any(
                    ref.id == item.id and ref.type == "text"
                    for ref in container.engine_element.boundElements or []
                ):
                    raise ValueError("Text containers must list their bound text.")

            if isinstance(item, CanvasEdge):
                for target_id, binding in (
                    (item.source_node_id, item.engine_element.startBinding),
                    (item.target_node_id, item.engine_element.endBinding),
                ):
                    if target_id is None:
                        if binding is not None:
                            raise ValueError("Free endpoints cannot have engine bindings.")
                        continue
                    target = by_id.get(target_id)
                    if not isinstance(target, (CanvasTextNode, CanvasShapeNode, CanvasImageNode)):
                        raise ValueError("Arrow endpoints must reference bindable nodes.")
                    if binding is None or binding.elementId != target_id:
                        raise ValueError("Canonical and engine endpoint references must match.")
                    if not any(
                        ref.id == item.id and ref.type == "arrow"
                        for ref in target.engine_element.boundElements or []
                    ):
                        raise ValueError("Arrow endpoints must list their bound arrow.")

        try:
            byte_size = len(self.model_dump_json().encode("utf-8"))
        except (PydanticSerializationError, UnicodeError) as exc:
            raise ValueError("Canvas document must contain valid UTF-8 JSON.") from exc
        if byte_size > MAX_CANVAS_DOCUMENT_BYTES:
            raise ValueError("Canvas document exceeds the UTF-8 JSON byte limit.")
        return self


class CanvasTagFields(BaseModel):
    tag_ids: list[UUID] = Field(default_factory=list, max_length=MAX_CANVAS_TAGS)

    @field_validator("tag_ids")
    @classmethod
    def unique_tag_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Canvas tag IDs must be unique.")
        return value


class CanvasCreateForm(CanvasTagFields):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    shelf_id: UUID
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    visibility: CanvasVisibility = "members"


class CanvasRevisionForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0, le=MAX_CANVAS_REVISION, strict=True)


class CanvasDocumentSaveForm(CanvasRevisionForm):
    """Expected revision belongs to the draft document, independently of metadata."""

    document: CanvasContent


class CanvasUnpublishForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_publication_revision: int = Field(ge=0, le=MAX_CANVAS_REVISION, strict=True)


class CanvasPublishForm(CanvasUnpublishForm):
    expected_metadata_revision: int = Field(ge=0, le=MAX_CANVAS_REVISION, strict=True)
    expected_document_revision: int = Field(ge=0, le=MAX_CANVAS_REVISION, strict=True)


def _patch_schema(schema: dict) -> None:
    for field in CANVAS_PATCH_FIELDS:
        schema["properties"][field].pop("default", None)
    schema["allOf"] = [{"anyOf": [{"required": [field]} for field in CANVAS_PATCH_FIELDS]}]


class CanvasPatchForm(CanvasRevisionForm, CanvasTagFields):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, json_schema_extra=_patch_schema
    )
    title: str = Field(default=None, min_length=1, max_length=200)
    summary: str = Field(default=None, max_length=500)
    shelf_id: UUID = None
    visibility: CanvasVisibility = None

    @model_validator(mode="after")
    def at_least_one_change(self):
        if not self.model_fields_set.intersection(CANVAS_PATCH_FIELDS):
            raise ValueError("Provide at least one canvas metadata field to change.")
        return self


class CanvasMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    board_id: UUID
    shelf_id: UUID
    author_id: int | None
    title: str
    summary: str
    visibility: CanvasVisibility
    status: CanvasStatus
    revision: int
    trashed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = Field(default_factory=list)

    @field_validator("created_at", "updated_at", "trashed_at")
    @classmethod
    def utc_datetimes(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None


class CanvasCapabilities(BaseModel):
    read_document: bool
    edit_metadata: bool
    edit_document: bool
    trash: bool
    restore: bool
    publish: bool = False
    unpublish: bool = False


class CanvasPublicationInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    publication_revision: int
    source_metadata_revision: int
    source_document_revision: int
    published_at: datetime

    @field_validator("published_at")
    @classmethod
    def utc_published_at(cls, value: datetime) -> datetime:
        return as_utc(value)


class CanvasResponse(BaseModel):
    canvas: CanvasMetadata
    document_revision: int
    view: Literal["draft"] = "draft"
    capabilities: CanvasCapabilities
    publication_revision: int = 0
    publication: CanvasPublicationInfo | None = None


class CanvasPublicationMetadata(BaseModel):
    id: UUID
    board_id: UUID
    shelf_id: UUID
    author_id: int | None
    title: str
    summary: str
    visibility: CanvasVisibility
    status: Literal["published"] = "published"
    tags: list[TagResponse]


class CanvasPublicationResponse(CanvasPublicationInfo):
    canvas: CanvasPublicationMetadata
    view: Literal["publication"] = "publication"
    capabilities: CanvasCapabilities


class CanvasPublicationDocumentResponse(CanvasPublicationInfo):
    document: CanvasContent
    revision: int
    view: Literal["publication"] = "publication"


class CanvasPublicationMutationResponse(BaseModel):
    metadata_revision: int
    document_revision: int
    publication_revision: int
    publication: CanvasPublicationInfo | None


class CanvasDocumentResponse(BaseModel):
    document: CanvasContent
    revision: int
    view: Literal["draft"] = "draft"


class CanvasDocumentSaveResponse(BaseModel):
    revision: int
    view: Literal["draft"] = "draft"


class CanvasDocumentValidationErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class CanvasDocumentValidationErrorResponse(BaseModel):
    # Match FastAPI's validation envelope alongside the domain-specific Asset 422.
    detail: list[CanvasDocumentValidationErrorDetail]


class CanvasMetadataValidationErrorResponse(BaseModel):
    detail: list[CanvasDocumentValidationErrorDetail]


class CanvasTransaction:
    def __init__(self, db: AsyncSession):
        self._db = db
        self.board = BoardTransaction(db)

    async def board_id(self, canvas_id: UUID) -> UUID | None:
        return await self._db.scalar(select(Canvas.board_id).where(Canvas.id == canvas_id))

    async def canvas(
        self, canvas_id: UUID, *, locked: bool = False, shared: bool = False
    ) -> Canvas | None:
        statement = select(Canvas).where(Canvas.id == canvas_id)
        return await self._db.scalar(
            statement.with_for_update(read=shared) if locked or shared else statement
        )

    async def document(self, canvas_id: UUID) -> CanvasDocument | None:
        return await self._db.get(CanvasDocument, canvas_id)

    async def tags(self, canvas_id: UUID) -> list[TagResponse]:
        return await TagTransaction(self._db).canvas_tags(canvas_id)

    async def publication(self, canvas_id: UUID) -> CanvasPublication | None:
        return await self._db.get(CanvasPublication, canvas_id)

    async def publication_revision(self, canvas_id: UUID) -> int:
        counter = await self._db.get(CanvasPublicationCounter, canvas_id)
        return counter.revision if counter is not None else 0

    async def publication_tags(self, canvas_id: UUID) -> list[TagResponse]:
        rows = (
            await self._db.scalars(
                select(CanvasPublicationTag)
                .where(CanvasPublicationTag.canvas_id == canvas_id)
                .order_by(CanvasPublicationTag.position)
            )
        ).all()
        return [TagResponse(id=row.tag_id, name=row.name) for row in rows]

    async def _advance_publication(self, canvas_id: UUID) -> int:
        counter = await self._db.get(CanvasPublicationCounter, canvas_id)
        if counter is None:
            counter = CanvasPublicationCounter(canvas_id=canvas_id, revision=0)
            self._db.add(counter)
        if counter.revision >= MAX_CANVAS_REVISION:
            raise CanvasException(
                CanvasErrorCode.PUBLICATION_CONFLICT, {"current_revision": counter.revision}
            )
        counter.revision += 1
        await self._db.flush()
        return counter.revision

    async def check_publication_revision(self, canvas_id: UUID, expected: int) -> int:
        current = await self.publication_revision(canvas_id)
        if current != expected:
            raise CanvasException(
                CanvasErrorCode.PUBLICATION_CONFLICT, {"current_revision": current}
            )
        return current

    async def publish(self, canvas: Canvas, form: CanvasPublishForm) -> CanvasPublication:
        from app.models.asset import AssetTransaction

        document = await self._db.scalar(
            select(CanvasDocument).where(CanvasDocument.canvas_id == canvas.id).with_for_update()
        )
        if document is None:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE)
        if canvas.revision != form.expected_metadata_revision:
            raise CanvasException(CanvasErrorCode.CONFLICT, {"current_revision": canvas.revision})
        if document.revision != form.expected_document_revision:
            raise CanvasException(
                CanvasErrorCode.DOCUMENT_CONFLICT, {"current_revision": document.revision}
            )
        await self.check_publication_revision(canvas.id, form.expected_publication_revision)
        try:
            content = CanvasContent.model_validate(document.document)
        except ValidationError as error:
            raise CanvasException(CanvasErrorCode.DOCUMENT_INVALID) from error
        publication = await self.publication(canvas.id)
        if publication is not None and (
            publication.source_metadata_revision == canvas.revision
            and publication.source_document_revision == document.revision
        ):
            return publication
        revision = await self._advance_publication(canvas.id)
        values = {
            "publication_revision": revision,
            "source_metadata_revision": canvas.revision,
            "source_document_revision": document.revision,
            "title": canvas.title,
            "summary": canvas.summary,
            "visibility": canvas.visibility,
            "document": content.model_dump(mode="json"),
            "published_at": utc_now(),
        }
        if publication is None:
            publication = CanvasPublication(canvas_id=canvas.id, **values)
            self._db.add(publication)
        else:
            for key, value in values.items():
                setattr(publication, key, value)
        await self._db.flush()
        await self._db.execute(
            delete(CanvasPublicationTag).where(CanvasPublicationTag.canvas_id == canvas.id)
        )
        self._db.add_all(
            [
                CanvasPublicationTag(
                    canvas_id=canvas.id, tag_id=tag.id, name=tag.name, position=index
                )
                for index, tag in enumerate(await self.tags(canvas.id))
            ]
        )
        await AssetTransaction(self._db).replace_refs(
            canvas,
            {node.content.asset_id for node in content.nodes if isinstance(node, CanvasImageNode)},
            scope="publication",
        )
        await self._db.flush()
        return publication

    async def unpublish(self, canvas: Canvas) -> None:
        from app.models.asset import AssetTransaction

        publication = await self.publication(canvas.id)
        if publication is None:
            return
        # Keep the common Document -> sorted Asset -> outbox order for both transitions.
        await self._db.scalar(
            select(CanvasDocument).where(CanvasDocument.canvas_id == canvas.id).with_for_update()
        )
        await self._advance_publication(canvas.id)
        await AssetTransaction(self._db).replace_refs(canvas, set(), scope="publication")
        await self._db.delete(publication)
        await self._db.flush()

    async def save_document(self, canvas: Canvas, form: CanvasDocumentSaveForm) -> int:
        # Same-session composition avoids a second transaction and circular initialization.
        from app.models.asset import AssetTransaction

        document = await self._db.scalar(
            select(CanvasDocument).where(CanvasDocument.canvas_id == canvas.id).with_for_update()
        )
        if document is None:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE)
        if document.revision != form.expected_revision or document.revision >= MAX_CANVAS_REVISION:
            raise CanvasException(
                CanvasErrorCode.DOCUMENT_CONFLICT, {"current_revision": document.revision}
            )
        revision = await self._db.scalar(
            update(CanvasDocument)
            .where(
                CanvasDocument.canvas_id == canvas.id,
                CanvasDocument.revision == form.expected_revision,
                CanvasDocument.revision < MAX_CANVAS_REVISION,
            )
            .values(
                document=form.document.model_dump(mode="json"),
                revision=CanvasDocument.revision + 1,
                updated_at=utc_now(),
            )
            .returning(CanvasDocument.revision)
        )
        if revision is None:
            current = await self._db.scalar(
                select(CanvasDocument.revision).where(CanvasDocument.canvas_id == canvas.id)
            )
            if current is None:
                raise CanvasException(CanvasErrorCode.UNAVAILABLE)
            raise CanvasException(CanvasErrorCode.DOCUMENT_CONFLICT, {"current_revision": current})
        asset_ids = {
            node.content.asset_id
            for node in form.document.nodes
            if isinstance(node, CanvasImageNode)
        }
        await AssetTransaction(self._db).replace_refs(canvas, asset_ids, scope="draft")
        return revision

    async def shelf(self, board_id: UUID, shelf_id: UUID) -> Shelf | None:
        return await self._db.scalar(
            select(Shelf).where(Shelf.board_id == board_id, Shelf.id == shelf_id)
        )

    async def create(self, board_id: UUID, user_id: int, form: CanvasCreateForm) -> Canvas:
        canvas = Canvas(
            board_id=board_id, author_id=user_id, **form.model_dump(exclude={"tag_ids"})
        )
        self._db.add(canvas)
        await self._db.flush()
        self._db.add(
            CanvasDocument(canvas_id=canvas.id, document=CanvasContent().model_dump(mode="json"))
        )
        await self._db.flush()
        await TagTransaction(self._db).replace_canvas_tags(canvas.id, form.tag_ids)
        return canvas

    async def patch(self, canvas: Canvas, form: CanvasPatchForm) -> None:
        changes = {
            key: getattr(form, key)
            for key in form.model_fields_set.intersection(CANVAS_FIELDS)
            if getattr(canvas, key) != getattr(form, key)
        }
        tags_changed = "tag_ids" in form.model_fields_set and await TagTransaction(
            self._db
        ).replace_canvas_tags(canvas.id, form.tag_ids)
        if not changes and not tags_changed:
            return
        for key, value in changes.items():
            setattr(canvas, key, value)
        self._touch(canvas)
        await self._db.flush()

    @staticmethod
    def _touch(canvas: Canvas) -> None:
        if canvas.revision >= MAX_CANVAS_REVISION:
            raise CanvasException(CanvasErrorCode.CONFLICT, {"current_revision": canvas.revision})
        canvas.revision += 1
        canvas.updated_at = utc_now()

    async def trash(self, canvas: Canvas) -> None:
        if canvas.status == "trashed":
            return
        await self.unpublish(canvas)
        canvas.status = "trashed"
        canvas.trashed_at = utc_now()
        self._touch(canvas)
        await self._db.flush()

    async def restore(self, canvas: Canvas) -> None:
        if canvas.status == "draft":
            return
        canvas.status, canvas.trashed_at = "draft", None
        self._touch(canvas)
        await self._db.flush()


class CanvasRepository:
    @asynccontextmanager
    async def transaction(self, *, write: bool = True) -> AsyncIterator[CanvasTransaction]:
        try:
            async with get_db() as db:
                if db.bind.dialect.name == "sqlite":
                    await db.execute(text("BEGIN IMMEDIATE" if write else "BEGIN"))
                yield CanvasTransaction(db)
                if write:
                    await db.commit()
        except SQLAlchemyError as error:
            raise CanvasException(CanvasErrorCode.UNAVAILABLE) from error
