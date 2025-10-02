import asyncio
from typing import Any, Dict
from urllib.parse import urlencode, urlsplit

import pytest

from app.api.routes.profile import get_profile_service
from app.main import app
from app.services.profile import ProfileService
from tests.conftest import FakeSupabaseProfileGateway


async def _request(
    method: str,
    raw_path: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, str]:
    parsed = urlsplit(raw_path)
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": parsed.path,
        "raw_path": raw_path.encode(),
        "query_string": parsed.query.encode(),
        "headers": [],
        "client": ("127.0.0.1", 0),
        "server": ("testserver", 80),
    }

    if headers:
        scope["headers"] = [
            (key.lower().encode(), value.encode()) for key, value in headers.items()
        ]

    messages: list[dict] = []

    body_bytes = body or b""
    body_sent = False

    async def receive() -> dict:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        body_sent = True
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, receive, send)

    status = next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    body = b"".join(
        message["body"] for message in messages if message["type"] == "http.response.body"
    )
    return status, body.decode()


def request(
    method: str,
    raw_path: str,
    headers: dict[str, str] | None = None,
    data: Dict[str, Any] | None = None,
) -> tuple[int, str]:
    encoded_body: bytes | None = None
    prepared_headers = dict(headers or {})
    if data is not None:
        encoded_body = urlencode(data, doseq=True).encode()
        prepared_headers.setdefault("content-type", "application/x-www-form-urlencoded")
    return asyncio.run(_request(method, raw_path, prepared_headers, encoded_body))


@pytest.fixture
def profile_service(fake_profile_gateway: FakeSupabaseProfileGateway) -> ProfileService:
    service = ProfileService(gateway=fake_profile_gateway)
    asyncio.run(service.reset_relationships())
    app.dependency_overrides[get_profile_service] = lambda: service
    return service


@pytest.fixture(autouse=True)
def cleanup_dependency_override() -> None:
    yield
    app.dependency_overrides.pop(get_profile_service, None)


def test_profile_detail_page_renders(profile_service: ProfileService) -> None:
    status, body = request("GET", "/profile/amelia-damayanti?viewer=user_chandra")

    assert status == 200
    assert "Amelia Damayanti" in body
    assert "Perfumer" in body


def test_profile_tab_endpoint_returns_perfumer_products(
    profile_service: ProfileService,
) -> None:
    status, body = request("GET", "/profile/amelia-damayanti/tab/karya")

    assert status == 200
    assert "Langit Sepia" in body


def test_follow_and_unfollow_flow_via_htmx(
    profile_service: ProfileService, fake_profile_gateway: FakeSupabaseProfileGateway
) -> None:
    status_follow, follow_body = request(
        "POST",
        "/profile/chandra-pratama/follow?viewer=user_bintang",
        headers={"hx-request": "true"},
    )
    assert status_follow == 200
    assert "Mengikuti" in follow_body
    assert ("user_bintang", "user_chandra") in fake_profile_gateway.follow_writes

    view = asyncio.run(profile_service.get_profile("chandra-pratama", viewer_id="user_bintang"))
    assert view.viewer.is_following is True

    status_unfollow, unfollow_body = request(
        "DELETE",
        "/profile/chandra-pratama/follow?viewer=user_bintang",
        headers={"hx-request": "true"},
    )
    assert status_unfollow == 200
    assert "Ikuti" in unfollow_body
    assert ("user_bintang", "user_chandra") in fake_profile_gateway.unfollow_writes

    view_after = asyncio.run(
        profile_service.get_profile("chandra-pratama", viewer_id="user_bintang")
    )
    assert view_after.viewer.is_following is False


def test_followers_modal_lists_profiles(profile_service: ProfileService) -> None:
    status, body = request("GET", "/profile/amelia-damayanti/followers")

    assert status == 200
    assert "Bintang Waskita" in body


def test_profile_edit_page_requires_owner(profile_service: ProfileService) -> None:
    status, body = request(
        "GET",
        "/profile/amelia-damayanti/edit?viewer=user_bintang",
    )

    assert status == 403
    assert "pemilik" in body


def test_profile_edit_page_renders_form(profile_service: ProfileService) -> None:
    status, body = request("GET", "/profile/amelia-damayanti/edit?viewer=user_amelia")

    assert status == 200
    assert "Perbarui Profil" in body
    assert "name=\"full_name\"" in body


def test_profile_update_submission_updates_gateway(
    profile_service: ProfileService, fake_profile_gateway: FakeSupabaseProfileGateway
) -> None:
    status, body = request(
        "PATCH",
        "/profile/amelia-damayanti?viewer=user_amelia",
        headers={"hx-request": "true"},
        data={
            "full_name": "Amelia Damayanti",
            "bio": "Perfumer independen & mentor komunitas.",
            "location": "Bandung, Indonesia",
            "preferred_aroma": "Rempah hangat",
            "avatar_url": "https://example.com/avatar.jpg",
        },
    )

    assert status == 200
    assert "Profil berhasil diperbarui" in body
    assert any(
        update.get("user_amelia") for update in fake_profile_gateway.profile_updates
    ), "Update payload should be recorded"

    view = asyncio.run(profile_service.get_profile("amelia-damayanti", viewer_id="user_amelia"))
    assert view.profile.bio == "Perfumer independen & mentor komunitas."
