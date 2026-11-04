"""Multipart lexical bounds, session/optional bearer and binary transport contracts."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_session_user, get_current_token_user
from app.main import register_exception_handlers
from app.models.board_media import BoardMediaSummary, BoardMediaUpdateResponse
from app.routers.v1.board_media import MAX_BOARD_MEDIA_REQUEST_BYTES, router
from app.services.board_media import BoardMediaService

pytestmark = pytest.mark.api_test
BOARD, ASSET = UUID(int=1), UUID(int=2)
PATH = f"/api/v1/boards/{BOARD}/media/cover"


@pytest.fixture
def media_api(sample_user):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_session_user] = lambda: sample_user
    app.dependency_overrides[get_current_token_user] = lambda: None
    service = AsyncMock(spec=BoardMediaService)
    service.upload.return_value = BoardMediaUpdateResponse(
        board_id=BOARD,
        slot="cover",
        media=BoardMediaSummary(
            id=ASSET,
            content_type="image/webp",
            byte_size=4,
            width=1,
            height=1,
            frame_count=1,
            created_at=datetime.now(UTC),
            url=PATH + f"/{ASSET}",
        ),
        board_revision=1,
        changed=True,
    )
    service.remove.return_value = BoardMediaUpdateResponse(
        board_id=BOARD, slot="cover", media=None, board_revision=2, changed=True
    )
    service.read.return_value = b"webp"
    app.dependency_overrides[BoardMediaService] = lambda: service
    return TestClient(app), service


@pytest.mark.parametrize(
    "revision", ["-1", "1.0", "1e0", "true", "+1", " 1", "١", "2147483648", "0" * 11]
)
def test_multipart_revision_is_ascii_integer_before_service(media_api, revision):
    client, service = media_api
    response = client.put(
        PATH,
        files={"file": ("x", b"x")},
        data={"expected_revision": revision, "reason": "이미지 변경"},
    )
    assert response.status_code == 422, response.text
    service.upload.assert_not_called()


@pytest.mark.parametrize("revision", [True, "0", 0.0, -1, 2**31])
def test_delete_strict_revision(media_api, revision):
    client, service = media_api
    assert (
        client.request(
            "DELETE", PATH, json={"expected_revision": revision, "reason": "삭제"}
        ).status_code
        == 422
    )
    service.remove.assert_not_called()


def test_single_file_bounded_multipart_and_versioned_bytes(media_api):
    client, service = media_api
    response = client.put(
        PATH,
        files={"file": ("x", b"x", "text/html")},
        data={"expected_revision": "0", "reason": " 변경 "},
    )
    assert response.status_code == 200, response.text
    assert response.headers["location"] == PATH + f"/{ASSET}"
    assert service.upload.call_args.args[3].expected_revision == 0
    assert service.upload.call_args.args[3].reason == "변경"
    service.upload.reset_mock()
    assert client.put(PATH, content=b"x" * (MAX_BOARD_MEDIA_REQUEST_BYTES + 1)).status_code == 413
    malformed = client.put(
        PATH,
        files=[("file", ("x", b"x")), ("file", ("y", b"y"))],
        data={"expected_revision": "0", "reason": "변경"},
    )
    assert malformed.status_code == 400 and isinstance(malformed.json()["detail"], str)
    service.upload.assert_not_called()
    assert (
        client.put(
            PATH.replace("cover", "other"),
            files={"file": ("x", b"x")},
            data={"expected_revision": "0", "reason": "변경"},
        ).status_code
        == 422
    )
    image = client.get(PATH + f"/{ASSET}")
    assert image.content == b"webp" and image.headers["content-type"] == "image/webp"
    assert (
        image.headers["cache-control"] == "private, no-store"
        and image.headers["x-content-type-options"] == "nosniff"
    )
    service.read.assert_awaited_once_with(None, BOARD, "cover", ASSET)
    schema = client.app.openapi()["paths"]
    assert schema["/api/v1/boards/{board_id}/media/{slot}"]["put"]["security"] == [
        {"OAuth2PasswordBearer": []}
    ]

    put = schema["/api/v1/boards/{board_id}/media/{slot}"]["put"]
    assert put["responses"]["400"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/BoardMediaMultipartError"
    )
