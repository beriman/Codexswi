import asyncio
from urllib.parse import urlsplit

import pytest

from app.api.routes.profile import get_profile_service
from app.main import app
from app.services.profile import ProfileService
from tests.conftest import FakeSupabaseProfileGateway


async def _request(method: str, raw_path: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
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

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

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


def request(method: str, raw_path: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
    return asyncio.run(_request(method, raw_path, headers))


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
