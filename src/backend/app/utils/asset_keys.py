"""Immutable application-owned image key namespaces shared by readers and cleanup."""

import re
from typing import Literal
from uuid import UUID

AssetNamespace = Literal["canvas-assets", "board-media"]


def valid_asset_key(key: str, asset_id: UUID, *, namespace: AssetNamespace | None = None) -> bool:
    prefix = re.escape(namespace) if namespace is not None else r"(?:canvas-assets|board-media)"
    return (
        re.fullmatch(rf"{prefix}/{re.escape(str(asset_id))}/[0-9a-f]{{32}}\.webp", key) is not None
    )
