"""Drain or retry a known asset cleanup job using the configured original storage."""

import argparse
import asyncio
import json
from uuid import UUID

from app.core.error.asset_exception import AssetException
from app.core.object_storage import StorageError
from app.services.asset_cleanup import run_asset_cleanup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--retry-id", type=UUID)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100.")
    try:
        result = asyncio.run(run_asset_cleanup(limit=args.limit, retry_id=args.retry_id))
    except (AssetException, StorageError, ValueError):
        parser.exit(
            1,
            "Asset cleanup failed; inspect the target schema and original storage configuration.\n",
        )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
