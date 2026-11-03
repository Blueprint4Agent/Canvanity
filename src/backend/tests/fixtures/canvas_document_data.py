"""Pinned engine output with real test Asset IDs for document-save scenarios."""

import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID


def canvas_document(*asset_ids: str | UUID) -> dict:
    document = json.loads(
        Path(__file__).with_name("canvas_content_v1.json").read_text(encoding="utf-8")
    )
    template = next(node for node in document["nodes"] if node["type"] == "image")
    nodes = [node for node in document["nodes"] if node["type"] != "image"]
    for index, asset_id in enumerate(asset_ids):
        image = deepcopy(template)
        image["id"] = image["engine_element"]["id"] = f"image-{index}"
        image["content"]["asset_id"] = str(asset_id)
        nodes.insert(2 + index, image)
    document["nodes"] = nodes
    document["element_order"] = [node["id"] for node in nodes] + [
        edge["id"] for edge in document["edges"]
    ]
    return document
