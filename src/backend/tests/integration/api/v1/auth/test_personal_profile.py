import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.config.settings import SETTINGS
from app.models.user import Users
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(SETTINGS, "REDIS_IN_MEMORY", True)


def login(client, email="profile@example.com"):
    client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
    response = client.post("/api/v1/auth/login", json=build_login_payload(email=email))
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}, response.json()["user"][
        "id"
    ]


def test_profile_fields_are_private_bounded_and_patch_preserves_omissions(integration_client):
    """Scenario: own profile changes persist without exposing other accounts or private credentials."""
    client = integration_client
    # Given: two separate signed-in accounts.
    headers, _ = login(client)
    other, _ = login(client, "other@example.com")
    # When: optional fields are saved, a later name-only patch preserves them.
    response = client.patch(
        "/api/v1/auth/me", headers=headers, json={"bio": "  Hello\nworld  ", "location": "KR:11"}
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Hello\nworld"
    assert response.json()["location"] == "KR:11"
    assert response.json()["has_password"] is True
    assert "password_hash" not in response.json()
    assert "profile_photo" not in response.json()
    client.patch("/api/v1/auth/me", headers=headers, json={"name": "New Name"})
    assert client.get("/api/v1/auth/me", headers=headers).json()["bio"] == "Hello\nworld"
    # Then: another account sees only its own blank profile; invalid writes preserve saved data.
    assert client.get("/api/v1/auth/me", headers=other).json()["bio"] is None
    for body in ({"bio": "x" * 101}, {"location": "x" * 101}, {"location": "US:11"}):
        assert client.patch("/api/v1/auth/me", headers=headers, json=body).status_code == 422
    assert client.patch("/api/v1/auth/me", json={"bio": "anonymous"}).status_code == 401
    cleared = client.patch("/api/v1/auth/me", headers=headers, json={"bio": None, "location": "  "})
    assert cleared.json()["bio"] is None and cleared.json()["location"] is None


def test_password_change_requires_own_single_use_email_code(integration_client, monkeypatch):
    """Scenario: deletion/other-account codes cannot change passwords and a valid code works once."""
    client = integration_client
    headers, user_id = login(client)
    other, _ = login(client, "other@example.com")
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    sender = AsyncMock()
    monkeypatch.setattr("app.services.auth.MAIL_QUEUE_SERVICE.enqueue_password_change", sender)
    # Given: issuance only uses the authenticated account's registered address.
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 200
    assert sender.call_args.kwargs["to_email"] == "profile@example.com"
    code = sender.call_args.kwargs["code"]
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 429
    body = {"code": code, "password": "NewPassword123!"}
    # When: another user or a deletion challenge tries to authorize the change.
    assert client.post("/api/v1/auth/me/password", headers=other, json=body).status_code == 400
    deletion_sender = AsyncMock()
    monkeypatch.setattr(
        "app.services.auth.MAIL_QUEUE_SERVICE.enqueue_account_deletion", deletion_sender
    )
    assert client.post("/api/v1/auth/me/deletion-code", headers=headers).status_code == 200
    deletion = deletion_sender.call_args.kwargs["code"]
    assert (
        client.post(
            "/api/v1/auth/me/password", headers=headers, json={**body, "code": deletion}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/me/password", headers=headers, json={**body, "password": "weak"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/auth/me/password/code/verify", headers=other, json={"code": code}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/me/password/code/verify", headers=headers, json={"code": code}
        ).status_code
        == 200
    )
    assert client.post("/api/v1/auth/me/password", headers=headers, json=body).status_code == 200
    assert client.post("/api/v1/auth/me/password", headers=headers, json=body).status_code == 400
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    assert (
        client.post(
            "/api/v1/auth/login", json=build_login_payload(email="profile@example.com")
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json=build_login_payload(email="profile@example.com", password=body["password"]),
        ).status_code
        == 200
    )


def test_email_disabled_blocks_all_email_proof_operations(integration_client):
    """Scenario: turning email off never creates an authentication bypass."""
    client = integration_client
    headers, _ = login(client)
    # Given/When: every proof-dependent endpoint is called with email disabled.
    operations = [
        ("POST", "/api/v1/auth/me/password/code", None),
        ("POST", "/api/v1/auth/me/password", {"code": "123456", "password": "NewPassword123!"}),
        ("POST", "/api/v1/auth/me/deletion-code", None),
        ("DELETE", "/api/v1/auth/me", {"email": "profile@example.com", "code": "123456"}),
        ("POST", "/api/v1/auth/forgot-password", {"email": "profile@example.com"}),
        ("POST", "/api/v1/auth/reset-password", {"token": "a" * 32, "password": "NewPassword123!"}),
    ]
    for method, path, body in operations:
        response = client.request(method, path, headers=headers, json=body)
        # Then: each request is rejected explicitly, while profile editing remains usable.
        assert response.json()["detail"]["error"] == "EMAIL_DISABLED"
    assert (
        client.patch("/api/v1/auth/me", headers=headers, json={"bio": "Still editable"}).status_code
        == 200
    )


def test_password_code_transport_rejects_anonymous_api_keys_and_mail_failure(
    integration_client, monkeypatch
):
    """Scenario: only bearer sessions can request proof and queue failures fail closed."""
    client = integration_client
    headers, user_id = login(client)
    key = client.post("/api/v1/api-keys", headers=headers, json={"name": "Profile test"})
    # Given: email is enabled but publication fails.
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(
        "app.services.auth.MAIL_QUEUE_SERVICE.enqueue_password_change",
        AsyncMock(side_effect=OSError("down")),
    )
    # When/Then: anonymous and key-only requests are unauthorized.
    assert client.post("/api/v1/auth/me/password/code").status_code == 401
    assert key.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/me/password/code", headers={"X-API-Key": key.json()["api_key"]}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 503
    assert asyncio.run(Users.get_auth_user_by_id(user_id)).password_hash


def test_handle_and_interests_persist_normalize_and_conflicts_are_atomic(integration_client):
    """Scenario: profile identity survives reads/login and duplicate handles roll back all edits."""
    client = integration_client
    headers, _ = login(client)
    other, _ = login(client, "other@example.com")
    saved = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"handle": " @Canvas_최혁 ", "interests": ["development", "ai", "development"]},
    )
    assert saved.status_code == 200
    assert saved.json()["handle"] == "canvas_최혁"
    assert saved.json()["interests"] == ["development", "ai"]
    assert client.get("/api/v1/auth/me", headers=headers).json()["handle"] == "canvas_최혁"
    again = client.post("/api/v1/auth/login", json=build_login_payload(email="profile@example.com"))
    assert again.json()["user"]["interests"] == ["development", "ai"]
    # Same owner may save its own handle; omitted identity fields survive unrelated edits.
    assert (
        client.patch("/api/v1/auth/me", headers=headers, json={"handle": "canvas_최혁"}).status_code
        == 200
    )
    client.patch("/api/v1/auth/me", headers=headers, json={"name": "New Name"})
    assert client.get("/api/v1/auth/me", headers=headers).json()["interests"] == [
        "development",
        "ai",
    ]
    conflict = client.patch(
        "/api/v1/auth/me", headers=other, json={"handle": "CANVAS_최혁", "bio": "must roll back"}
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["error"] == "HANDLE_ALREADY_EXISTS"
    assert client.get("/api/v1/auth/me", headers=other).json()["bio"] is None
    assert client.get("/api/v1/auth/me", headers=other).json()["interests"] == []
    # Clearing releases the handle; multiple accounts may keep no handle.
    cleared = client.patch(
        "/api/v1/auth/me", headers=headers, json={"handle": None, "interests": []}
    )
    assert cleared.json()["handle"] is None and cleared.json()["interests"] == []
    assert (
        client.patch("/api/v1/auth/me", headers=other, json={"handle": "canvas_최혁"}).status_code
        == 200
    )


@pytest.mark.parametrize(
    "body",
    [
        {"handle": "x"},
        {"handle": "two words"},
        {"handle": "x" * 25},
        {"handle": "<script>"},
        {"interests": ["x"] * 9},
        {"interests": ["x" * 21]},
        {"interests": ["   "]},
        {"interests": [123]},
        {"interests": None},
    ],
)
def test_invalid_profile_identity_preserves_saved_values(integration_client, body):
    """Scenario: invalid handles/tags return 422 without partially changing identity."""
    headers, _ = login(integration_client)
    integration_client.patch("/api/v1/auth/me", headers=headers, json={"handle": "safe_handle"})
    assert (
        integration_client.patch("/api/v1/auth/me", headers=headers, json=body).status_code == 422
    )
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers).json()["handle"] == "safe_handle"
    )


def test_official_catalog_is_public_but_only_admins_manage_and_members_select(integration_client):
    """Scenario: official taxonomy is shared, stable and writable only by platform admins."""
    from app.models.user import UserRole

    client = integration_client
    catalog = client.get("/api/v1/interests")
    assert catalog.status_code == 200 and len(catalog.json()["items"]) == 40
    assert catalog.json()["items"][0]["id"] == "daily"
    assert {"pets", "fashion", "beauty", "home", "sports", "coffee", "camping"}.issubset(
        {item["id"] for item in catalog.json()["items"]}
    )
    ai = next(item for item in catalog.json()["items"] if item["id"] == "ai")
    assert "인공지능" in ai["aliases"]
    admin, _ = login(client, "catalog-admin@example.com")
    member, _ = login(client, "catalog-member@example.com")
    asyncio.run(
        Users.set_operator_role("catalog-admin@example.com", UserRole.ADMIN, operator="test")
    )
    # A status-only update must preserve aliases assigned before a specific category existed.
    assert (
        client.patch(
            "/api/v1/interests/admin/sports", headers=admin, json={"active": False}
        ).status_code
        == 200
    )
    assert (
        client.patch(
            "/api/v1/interests/admin/sports", headers=admin, json={"active": True}
        ).status_code
        == 200
    )
    body = {"id": "robotics", "name_ko": "로봇공학", "name_en": "Robotics", "aliases": ["robots"]}
    assert client.post("/api/v1/interests/admin", json=body).status_code == 401
    assert client.post("/api/v1/interests/admin", headers=member, json=body).status_code == 403
    assert client.post("/api/v1/interests/admin", headers=admin, json=body).status_code == 201
    assert client.post("/api/v1/interests/admin", headers=admin, json=body).status_code == 409
    assert (
        client.patch(
            "/api/v1/auth/me", headers=member, json={"interests": ["robotics", "ai"]}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/auth/me", headers=member).json()["interests"] == ["robotics", "ai"]
    assert (
        client.patch(
            "/api/v1/interests/admin/robotics", headers=member, json={"active": False}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            "/api/v1/interests/admin/robotics", headers=admin, json={"active": False}
        ).status_code
        == 200
    )
    assert "robotics" not in [
        item["id"] for item in client.get("/api/v1/interests").json()["items"]
    ]
    invalid = client.patch(
        "/api/v1/auth/me", headers=member, json={"interests": ["robotics"], "bio": "must roll back"}
    )
    assert (
        invalid.status_code == 422 and invalid.json()["detail"]["error"] == "INTEREST_NOT_AVAILABLE"
    )
    assert client.get("/api/v1/auth/me", headers=member).json()["bio"] is None
    assert (
        client.patch(
            "/api/v1/auth/me", headers=member, json={"interests": ["new-user-topic"]}
        ).status_code
        == 422
    )
    admin_items = client.get("/api/v1/interests/admin", headers=admin).json()
    assert next(item for item in admin_items if item["id"] == "robotics")["active"] is False
    assert (
        client.patch(
            "/api/v1/interests/admin/missing", headers=admin, json={"active": False}
        ).status_code
        == 404
    )
