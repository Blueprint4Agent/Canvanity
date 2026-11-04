"""Strict UI-widget documents, separate from Content Canvas engine documents."""

import json
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.board_layout_limits import (
    MAX_BOARD_LAYOUT_BYTES,
    MAX_BOARD_LAYOUT_REVISION,
    MAX_BOARD_LAYOUT_WIDGETS,
)


class LayoutModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class BoardWidgetPosition(LayoutModel):
    x: float = Field(strict=True, ge=-100_000, le=100_000)
    y: float = Field(strict=True, ge=-100_000, le=100_000)


class BoardWidgetSize(LayoutModel):
    width: float = Field(strict=True, gt=0, le=100_000)
    height: float = Field(strict=True, gt=0, le=100_000)


class BoardWidgetBase(LayoutModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    position: BoardWidgetPosition
    size: BoardWidgetSize


class BoardIntroWidget(BoardWidgetBase):
    type: Literal["board_intro"]


class BoardCoverWidget(BoardWidgetBase):
    type: Literal["board_cover"]


class ShelfNavigationWidget(BoardWidgetBase):
    type: Literal["shelf_navigation"]


class BoardCollectionSource(LayoutModel):
    board_id: UUID
    shelf_id: UUID | None = None
    sort: Literal["latest"] = "latest"
    limit: int = Field(default=6, strict=True, ge=1, le=20)


class CanvasCollectionWidget(BoardWidgetBase):
    type: Literal["canvas_collection"]
    source: BoardCollectionSource


BoardWidget = Annotated[
    BoardIntroWidget | BoardCoverWidget | ShelfNavigationWidget | CanvasCollectionWidget,
    Field(discriminator="type"),
]


class BoardLayoutDocument(LayoutModel):
    schema_version: int = Field(strict=True, ge=1, le=1)
    widgets: list[BoardWidget] = Field(max_length=MAX_BOARD_LAYOUT_WIDGETS)

    @model_validator(mode="after")
    def bounded_document(self):
        ids = [widget.id for widget in self.widgets]
        if len(set(ids)) != len(ids):
            raise ValueError("Widget IDs must be unique.")
        if len(self.canonical_bytes()) > MAX_BOARD_LAYOUT_BYTES:
            raise ValueError("Layout exceeds 256 KiB.")
        return self

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.model_dump(mode="json", exclude_none=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")


class BoardLayoutSaveForm(LayoutModel):
    expected_revision: int = Field(strict=True, ge=0, le=MAX_BOARD_LAYOUT_REVISION)
    document: BoardLayoutDocument
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def meaningful_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Provide an audit reason.")
        return value


class BoardLayoutResponse(LayoutModel):
    board_id: UUID
    document: BoardLayoutDocument
    layout_revision: int = Field(ge=0, le=MAX_BOARD_LAYOUT_REVISION)


class BoardLayoutAuditChange(LayoutModel):
    before_revision: int
    after_revision: int
    before_hash: str
    after_hash: str
    widget_count: int
