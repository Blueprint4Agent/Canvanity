"""Visitor projection and ephemeral data for the official Board home."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.board import BoardSummary, GradeSummary, MembershipSummary, ShelfSummary
from app.models.board_layout import BoardLayoutDocument
from app.models.board_media import BoardMediaSummary
from app.models.canvas_feed import CanvasFeedItem


class BoardIntroData(BaseModel):
    id: str
    type: Literal["board_intro"] = "board_intro"
    board: BoardSummary
    rules: str


class BoardCoverData(BaseModel):
    id: str
    type: Literal["board_cover"] = "board_cover"
    media: BoardMediaSummary | None = None


class ShelfNavigationData(BaseModel):
    id: str
    type: Literal["shelf_navigation"] = "shelf_navigation"
    shelves: list[ShelfSummary]


class CanvasCollectionData(BaseModel):
    id: str
    type: Literal["canvas_collection"] = "canvas_collection"
    items: list[CanvasFeedItem] = Field(max_length=20)


BoardWidgetData = Annotated[
    BoardIntroData | BoardCoverData | ShelfNavigationData | CanvasCollectionData,
    Field(discriminator="type"),
]


class BoardHomeResponse(BaseModel):
    board: BoardSummary
    rules: str
    membership: MembershipSummary | None
    grades: list[GradeSummary]
    shelves: list[ShelfSummary]
    layout: BoardLayoutDocument
    layout_revision: int
    widget_data: list[BoardWidgetData] = Field(max_length=100)
    can_manage_media: bool = False
