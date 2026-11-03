"""Content v1 contract cases, using an export from the pinned real engine."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.canvas import (
    MAX_CANVAS_DOCUMENT_BYTES,
    MAX_CANVAS_ELEMENTS,
    MAX_CANVAS_POINTS,
    MAX_CANVAS_TEXT_LENGTH,
    CanvasContent,
    CanvasDrawingNode,
    CanvasImageNode,
    CanvasShapeNode,
    CanvasTextNode,
)

FIXTURE = Path(__file__).parents[2] / "fixtures" / "canvas_content_v1.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def set_path(data, path, value):
    parts = path.split(".")
    for key in parts[:-1]:
        data = data[int(key)] if isinstance(data, list) else data[key]
    key = parts[-1]
    data[int(key) if isinstance(data, list) else key] = value


def test_real_engine_export_retains_five_types_geometry_text_and_order():
    raw = document()
    model = CanvasContent.model_validate(raw)
    assert [type(node) for node in model.nodes] == [
        CanvasTextNode,
        CanvasShapeNode,
        CanvasImageNode,
        CanvasDrawingNode,
    ]
    assert model.nodes[0].engine_element.text == "한글 캔버스\n저장 후 다시 편집"
    assert model.model_dump(mode="json") == raw
    assert CanvasContent.model_validate_json(model.model_dump_json()) == model


def test_existing_empty_document_remains_identical():
    raw = document()
    raw.update(nodes=[], edges=[], element_order=[])
    assert CanvasContent().model_dump(mode="json") == raw


@pytest.mark.parametrize(
    "path,value",
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", "1"),
        ("engine.version", "0.19.0"),
        ("engine.adapter_version", True),
        ("engine.adapter_version", 2),
        ("engine.name", "other"),
        ("settings.width", 0),
        ("settings.height", True),
        ("settings.width", "3200"),
        ("settings.grid", "custom"),
        ("settings.background", "url(https://example.invalid/image)"),
        ("widgets", []),
        ("selectedElementIds", {}),
        ("nodes.0.id", ""),
        ("nodes.0.id", "x" * 81),
        ("nodes.0.position.x", float("nan")),
        ("nodes.0.position.y", float("inf")),
        ("nodes.0.position.x", True),
        ("nodes.0.size.width", -1),
        ("nodes.0.position.x", 100_001),
        ("nodes.0.engine_element.text", "x" * (MAX_CANVAS_TEXT_LENGTH + 1)),
        ("nodes.0.engine_element.originalText", "x" * (MAX_CANVAS_TEXT_LENGTH + 1)),
        ("nodes.0.engine_element.text", "\ud800"),
        ("nodes.0.engine_element.fontFamily", 4),
        ("nodes.0.engine_element.fontFamily", True),
        ("nodes.0.engine_element.fontSize", 0),
        ("nodes.1.engine_element.type", "frame"),
        ("nodes.1.engine_element.strokeColor", "javascript:alert(1)"),
        ("nodes.1.engine_element.opacity", 101),
        ("nodes.1.engine_element.strokeWidth", "2"),
        ("nodes.1.engine_element.customData", {"html": "<script>"}),
        ("nodes.1.engine_element.link", "https://example.invalid"),
        ("nodes.1.engine_element.groupIds", ["group-one"]),
        ("nodes.1.engine_element.frameId", "frame-one"),
        ("nodes.1.engine_element.isDeleted", True),
        ("nodes.1.engine_element.isDeleted", 0),
        ("nodes.1.engine_element.version", True),
        ("nodes.1.engine_element.updated", 2**53),
        ("nodes.2.content.asset_id", "https://example.invalid/image.png"),
        ("nodes.2.content.data_url", "data:image/png;base64,AAAA"),
        ("nodes.2.engine_element.fileId", "temporary-file"),
        ("nodes.2.engine_element.status", "pending"),
        ("nodes.2.engine_element.scale", [True, 1]),
        ("nodes.2.engine_element.scale", [0, 1]),
        ("nodes.3.engine_element.points", []),
        ("nodes.3.engine_element.points", [[0, 0, 1]]),
        ("nodes.3.engine_element.points", [[0, float("nan")]]),
        ("nodes.3.engine_element.pressures", [0.5]),
        ("nodes.3.engine_element.pressures", [1.1] * 4),
        ("nodes.3.engine_element.simulatePressure", "false"),
        ("edges.0.engine_element.points", [[0, 0]]),
        ("edges.0.engine_element.elbowed", True),
        ("edges.0.source_node_id", "missing-node"),
        ("edges.0.target_node_id", "draw-one"),
        ("edges.0.target_node_id", "edge-one"),
    ],
)
def test_rejects_unsupported_versions_types_hidden_data_and_invalid_values(path, value):
    raw = document()
    set_path(raw, path, value)
    with pytest.raises(ValidationError):
        CanvasContent.model_validate(raw)


@pytest.mark.parametrize(
    "path,value",
    [
        ("nodes.0.engine_element.id", "different-id"),
        ("nodes.0.engine_element.x", 42),
        ("nodes.0.engine_element.y", 42),
        ("nodes.0.engine_element.width", 42),
        ("nodes.0.engine_element.height", 42),
    ],
)
def test_rejects_duplicate_geometry_that_disagrees_with_the_engine(path, value):
    raw = document()
    set_path(raw, path, value)
    with pytest.raises(ValidationError, match="identity/geometry must match"):
        CanvasContent.model_validate(raw)


@pytest.mark.parametrize("order", [[], ["missing"], ["text-one"] * 5])
def test_order_must_cover_all_nodes_and_edges_exactly_once(order):
    raw = document()
    raw["element_order"] = order
    with pytest.raises(ValidationError, match="Element order"):
        CanvasContent.model_validate(raw)


def test_node_and_edge_ids_share_one_namespace():
    raw = document()
    raw["edges"][0]["id"] = raw["edges"][0]["engine_element"]["id"] = "text-one"
    with pytest.raises(ValidationError, match="IDs must be unique"):
        CanvasContent.model_validate(raw)


def connected_document():
    raw = document()
    edge = raw["edges"][0]
    for key, field, node in [
        ("source_node_id", "startBinding", raw["nodes"][1]),
        ("target_node_id", "endBinding", raw["nodes"][0]),
    ]:
        edge[key] = node["id"]
        edge["engine_element"][field] = {"elementId": node["id"], "focus": 0, "gap": 5}
        node["engine_element"]["boundElements"] = [{"id": edge["id"], "type": "arrow"}]
    return raw


def test_bound_arrows_and_text_containers_preserve_reciprocal_references():
    raw = connected_document()
    raw["nodes"][0]["engine_element"]["containerId"] = "shape-one"
    raw["nodes"][1]["engine_element"]["boundElements"].append({"id": "text-one", "type": "text"})
    model = CanvasContent.model_validate(raw)
    assert model.model_dump(mode="json") == raw


@pytest.mark.parametrize(
    "path,value",
    [
        ("edges.0.source_node_id", None),
        ("edges.0.engine_element.startBinding", None),
        ("edges.0.engine_element.startBinding.elementId", "text-one"),
        ("nodes.1.engine_element.boundElements", []),
        ("nodes.1.engine_element.boundElements", [{"id": "missing", "type": "arrow"}]),
        ("nodes.0.engine_element.containerId", "missing"),
        ("nodes.0.engine_element.containerId", "draw-one"),
        ("nodes.0.engine_element.containerId", "shape-one"),
    ],
)
def test_bindings_reject_dangling_mismatched_and_one_way_references(path, value):
    raw = connected_document()
    set_path(raw, path, value)
    with pytest.raises(ValidationError):
        CanvasContent.model_validate(raw)


def test_free_line_and_horizontal_drawing_are_supported():
    raw = document()
    line = raw["edges"][0]
    line["engine_element"]["type"] = "line"
    line["engine_element"].pop("elbowed")
    line["size"]["height"] = line["engine_element"]["height"] = 0
    line["engine_element"]["points"] = [[0, 0], [79, 0]]
    drawing = raw["nodes"][3]
    drawing["size"]["height"] = drawing["engine_element"]["height"] = 0
    drawing["engine_element"].update(points=[[0, 0], [120, 0]], pressures=[], simulatePressure=True)
    assert CanvasContent.model_validate(raw).edges[0].size.height == 0


@pytest.mark.parametrize("node_index", [0, 1, 2, 3])
def test_zero_extent_is_rejected_even_when_both_geometry_copies_agree(node_index):
    raw = document()
    item = raw["nodes"][node_index]
    item["size"].update(width=0, height=0)
    item["engine_element"].update(width=0, height=0)
    with pytest.raises(ValidationError, match="non-zero extent"):
        CanvasContent.model_validate(raw)


def test_image_flip_and_crop_have_bounded_numeric_fields():
    raw = document()
    image = raw["nodes"][2]["engine_element"]
    image.update(
        scale=[-1, 1],
        crop={"x": 1, "y": 2, "width": 10, "height": 20, "naturalWidth": 16, "naturalHeight": 32},
    )
    assert CanvasContent.model_validate(raw).nodes[2].engine_element.crop.width == 10
    image["crop"]["x"] = 7
    with pytest.raises(ValidationError, match="crop must fit"):
        CanvasContent.model_validate(raw)


def test_total_limit_applies_to_nodes_and_edges_combined():
    raw = document()
    shape = raw["nodes"][1]
    raw["nodes"] = []
    raw["edges"] = []
    for index in range(MAX_CANVAS_ELEMENTS):
        node = deepcopy(shape)
        node["id"] = node["engine_element"]["id"] = f"shape-{index}"
        raw["nodes"].append(node)
    raw["element_order"] = [item["id"] for item in raw["nodes"]]
    assert len(CanvasContent.model_validate(raw).nodes) == MAX_CANVAS_ELEMENTS
    raw["edges"] = document()["edges"]
    raw["element_order"].append("edge-one")
    with pytest.raises(ValidationError, match="total element limit"):
        CanvasContent.model_validate(raw)


def test_point_and_text_limits_accept_boundaries_and_reject_one_more():
    raw = document()
    text = raw["nodes"][0]["engine_element"]
    text["text"] = text["originalText"] = "한" * MAX_CANVAS_TEXT_LENGTH
    drawing = raw["nodes"][3]
    drawing["size"].update(width=MAX_CANVAS_POINTS - 1, height=99)
    drawing["engine_element"].update(
        width=MAX_CANVAS_POINTS - 1,
        height=99,
        points=[[i, i % 100] for i in range(MAX_CANVAS_POINTS)],
        pressures=[],
        simulatePressure=True,
    )
    assert (
        len(CanvasContent.model_validate(raw).nodes[3].engine_element.points) == MAX_CANVAS_POINTS
    )
    drawing["engine_element"]["points"].append([0, 0])
    with pytest.raises(ValidationError):
        CanvasContent.model_validate(raw)


def test_document_limit_counts_utf8_bytes_rather_than_characters():
    raw = document()
    text = raw["nodes"][0]
    text["engine_element"]["text"] = text["engine_element"]["originalText"] = (
        "한" * MAX_CANVAS_TEXT_LENGTH
    )
    raw["nodes"] = []
    raw["edges"] = []
    for index in range(20):
        node = deepcopy(text)
        node["id"] = node["engine_element"]["id"] = f"text-{index}"
        raw["nodes"].append(node)
    raw["element_order"] = [item["id"] for item in raw["nodes"]]
    assert len(json.dumps(raw, ensure_ascii=False)) < MAX_CANVAS_DOCUMENT_BYTES
    with pytest.raises(ValidationError, match="UTF-8 JSON byte limit"):
        CanvasContent.model_validate(raw)
