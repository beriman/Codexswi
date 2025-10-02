import asyncio
from typing import Any, Dict
from urllib.parse import urlencode, urlsplit

import pytest

from app.api.routes import brands as brand_routes
from app.main import app
from app.services import brands as brand_service_module
from app.services.brands import Brand, BrandService


async def _request(
    method: str,
    raw_path: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], str]:
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

    messages: list[dict[str, Any]] = []

    body_bytes = body or b""
    body_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        body_sent = True
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(scope, receive, send)

    start_message = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    status = start_message["status"]
    response_headers = {
        key.decode(): value.decode() for key, value in start_message.get("headers", [])
    }
    body = b"".join(
        message["body"] for message in messages if message["type"] == "http.response.body"
    )
    return status, response_headers, body.decode()


def request(
    method: str,
    raw_path: str,
    headers: dict[str, str] | None = None,
    data: Dict[str, Any] | None = None,
) -> tuple[int, dict[str, str], str]:
    encoded_body: bytes | None = None
    prepared_headers = dict(headers or {})
    if data is not None:
        encoded_body = urlencode(data, doseq=True).encode()
        prepared_headers.setdefault("content-type", "application/x-www-form-urlencoded")
    return asyncio.run(_request(method, raw_path, prepared_headers, encoded_body))


@pytest.fixture(autouse=True)
def reset_brand_service() -> None:
    service = BrandService()
    brand_service_module.brand_service = service
    brand_routes.brand_service = service
    yield
    refreshed = BrandService()
    brand_service_module.brand_service = refreshed
    brand_routes.brand_service = refreshed


def build_form_payload(brand: Brand, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": brand.name,
        "slug": brand.slug,
        "tagline": brand.tagline,
        "summary": brand.summary,
        "origin_city": brand.origin_city,
        "established_year": str(brand.established_year),
        "hero_image_url": brand.hero_image_url,
        "logo_url": brand.logo_url or "",
        "aroma_focus": "\n".join(brand.aroma_focus),
        "story_points": "\n".join(brand.story_points),
    }
    if brand.is_verified:
        payload["is_verified"] = "1"

    for index, member in enumerate(brand.members):
        prefix = f"members-{index}-"
        payload[f"{prefix}profile_id"] = member.profile_id
        payload[f"{prefix}full_name"] = member.full_name
        payload[f"{prefix}username"] = member.username
        payload[f"{prefix}role"] = member.role
        payload[f"{prefix}status"] = member.status
        payload[f"{prefix}avatar_url"] = member.avatar_url or ""
        payload[f"{prefix}expertise"] = member.expertise or ""
        payload[f"{prefix}invited_by"] = member.invited_by or ""

    if overrides:
        payload.update(overrides)

    return payload


def test_new_brand_form_renders(reset_brand_service: None) -> None:
    status, _, body = request("GET", "/brands/new")

    assert status == 200
    assert "Buat Brand Baru" in body
    assert "Nama brand" in body


def test_create_brand_flow(reset_brand_service: None) -> None:
    data = {
        "name": "Aroma Harmoni",
        "slug": "aroma-harmoni",
        "tagline": "Eksplorasi aroma herbal",
        "summary": "Brand eksperimen aroma yang fokus pada bahan botani.",
        "origin_city": "Semarang, Indonesia",
        "established_year": "2022",
        "hero_image_url": "https://example.com/hero.jpg",
        "logo_url": "https://example.com/logo.png",
        "aroma_focus": "Herbal\nFermentasi",
        "story_points": "Riset aroma lokal\nMengembangkan komunitas tester",
        "is_verified": "1",
        "members-0-profile_id": "owner_diah",
        "members-0-full_name": "Diah Lestari",
        "members-0-username": "diah-lestari",
        "members-0-role": "owner",
        "members-0-status": "active",
        "members-0-avatar_url": "",
        "members-0-expertise": "Pendiri",
        "members-0-invited_by": "",
        "members-1-profile_id": "co_harmoni",
        "members-1-full_name": "Ari Pratama",
        "members-1-username": "ari-pratama",
        "members-1-role": "co-owner",
        "members-1-status": "pending",
        "members-1-avatar_url": "",
        "members-1-expertise": "Community",
        "members-1-invited_by": "Diah Lestari",
    }

    status, headers, _ = request("POST", "/brands", data=data)

    assert status == 303
    assert headers.get("location") == "/brands/aroma-harmoni"

    created = brand_service_module.brand_service.get_brand("aroma-harmoni")
    assert created.name == "Aroma Harmoni"
    assert any(member.username == "ari-pratama" for member in created.members)


def test_edit_brand_form_prefills_existing_data(reset_brand_service: None) -> None:
    status, _, body = request("GET", "/brands/langit-senja/edit")

    assert status == 200
    assert "Langit Senja" in body
    assert "langit-senja" in body


def test_update_brand_flow_and_redirect(reset_brand_service: None) -> None:
    service_brand = brand_service_module.brand_service.get_brand("langit-senja")
    payload = build_form_payload(
        service_brand,
        overrides={
            "name": "Langit Senja Baru",
            "slug": "langit-senja-baru",
            "tagline": "Cerita aroma baru",
            "origin_city": "Bandung, Indonesia",
            "story_points": "Cerita baru",
            "aroma_focus": "Rempah\nGourmand",
            "is_verified": "1",
        },
    )

    status, headers, _ = request("POST", "/brands/langit-senja", data=payload)

    assert status == 303
    assert headers.get("location") == "/brands/langit-senja-baru?updated=1"

    updated = brand_service_module.brand_service.get_brand("langit-senja-baru")
    assert updated.name == "Langit Senja Baru"
    assert updated.slug == "langit-senja-baru"


def test_update_brand_duplicate_slug_validation(reset_brand_service: None) -> None:
    service_brand = brand_service_module.brand_service.get_brand("studio-senja")
    payload = build_form_payload(service_brand, overrides={"slug": "langit-senja"})

    status, _, body = request("POST", "/brands/studio-senja", data=payload)

    assert status == 400
    assert "Slug brand sudah digunakan" in body
    assert brand_service_module.brand_service.get_brand("studio-senja").slug == "studio-senja"


def test_create_brand_duplicate_slug_validation(reset_brand_service: None) -> None:
    data = {
        "name": "Brand Duplikat",
        "slug": "langit-senja",
        "tagline": "Tagline",
        "summary": "Ringkasan",
        "origin_city": "Jakarta",
        "established_year": "2023",
        "hero_image_url": "https://example.com/hero.png",
        "aroma_focus": "",
        "story_points": "",
        "members-0-profile_id": "owner_duplicate",
        "members-0-full_name": "Owner Baru",
        "members-0-username": "owner-baru",
        "members-0-role": "owner",
        "members-0-status": "active",
        "members-0-avatar_url": "",
        "members-0-expertise": "",
        "members-0-invited_by": "",
    }

    status, _, body = request("POST", "/brands", data=data)

    assert status == 400
    assert "Nama brand sudah digunakan" in body or "Slug brand sudah digunakan" in body
