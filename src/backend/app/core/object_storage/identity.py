"""Nonsecret storage locations; fingerprints retain the existing profile-photo format."""

import hashlib
import json
from dataclasses import dataclass

from app.core.config.settings import SETTINGS, Settings


@dataclass(frozen=True)
class StorageLocation:
    fingerprint: str
    descriptor: dict[str, str]


def object_storage_location(settings: Settings) -> StorageLocation:
    provider = settings.OBJECT_STORAGE_PROVIDER
    source = [provider]
    descriptor = {"provider": provider}
    if provider == "local":
        root = str(settings.OBJECT_STORAGE_LOCAL_ROOT.resolve())
        source.append(root)
        descriptor["root"] = root
    else:
        endpoint = settings.OBJECT_STORAGE_S3_ENDPOINT_URL.rstrip("/")
        bucket = settings.OBJECT_STORAGE_S3_BUCKET
        region = settings.OBJECT_STORAGE_S3_REGION if provider != "r2" else "auto"
        source.extend([endpoint, bucket, region])
        descriptor.update(endpoint=endpoint, bucket=bucket, region=region)
    return StorageLocation(hashlib.sha256(json.dumps(source).encode()).hexdigest(), descriptor)


def storage_identity() -> str:
    return object_storage_location(SETTINGS).fingerprint
