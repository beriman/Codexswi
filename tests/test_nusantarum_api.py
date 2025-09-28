"""API tests for Nusantarum router without relying on external HTTP clients."""
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import asyncio

import pytest

from app.api.routes.nusantarum import get_service
from app.main import app
from app.services.nusantarum_service import (
    BrandListItem,
    NusantarumConfigurationError,
    PagedResult,
    PerfumeListItem,
    PerfumerListItem,
    SyncLog,
)


class FakeNusantarumService:
    def __init__(self) -> None:
        self.triggered: List[str] = []

    async def list_perfumes(self, **_: Any) -> PagedResult:
        perfume = PerfumeListItem(
            id="pf-1",
            name="Hutan Senja",
            slug="hutan-senja",
            brand_name="Langit Senja",
            brand_slug="langit-senja",
            brand_city="Bandung",
            brand_profile_username="langit-senja",
            perfumer_name="Ayu Pratiwi",
            perfumer_slug="ayu-pratiwi",
            perfumer_profile_username="ayu-pratiwi",
            hero_note="Jasmine dan kayu cendana",
            description="Aroma nostalgia senja di hutan pinus.",
            aroma_families=["Floral", "Woody"],
            price_reference=450000,
            price_currency="IDR",
            marketplace_price=470000,
            marketplace_status="published",
            marketplace_product_id="prod-1",
            base_image_url="https://cdn.example.com/hutan-senja.jpg",
            sync_source="marketplace",
            sync_status="success",
            synced_at=None,
            updated_at=None,
            marketplace_rating=4.7,
        )
        return PagedResult(items=[perfume], total=1, page=1, page_size=12)

    async def list_brands(self, **_: Any) -> PagedResult:
        brand = BrandListItem(
            id="brand-1",
            name="Langit Senja",
            slug="langit-senja",
            origin_city="Bandung",
            active_perfume_count=3,
            nusantarum_status="aktif",
            brand_profile_username="langit-senja",
            last_perfume_synced_at=None,
        )
        return PagedResult(items=[brand], total=1, page=1, page_size=12)

    async def list_perfumers(self, **_: Any) -> PagedResult:
        perfumer = PerfumerListItem(
            id="pfmr-1",
            display_name="Ayu Pratiwi",
            slug="ayu-pratiwi",
            signature_scent="Tropical jasmine",
            active_perfume_count=2,
            perfumer_profile_username="ayu-pratiwi",
            highlight_perfume="Hutan Senja",
            highlight_brand="Langit Senja",
            last_synced_at=None,
        )
        return PagedResult(items=[perfumer], total=1, page=1, page_size=12)

    async def search(self, query: str, limit: int = 5) -> Dict[str, List[str]]:
        return {
            "perfumes": [f"{query.title()} Parfum"],
            "brands": [f"{query.title()} Brand"],
            "perfumers": [f"{query.title()} Perfumer"],
        }

    async def get_sync_status(self) -> List[SyncLog]:
        return [
            SyncLog(
                source="marketplace",
                status="success",
                summary="Synced",
                run_at=datetime(2024, 4, 2, 10, 0, 0),
            )
        ]

    async def trigger_sync(self, source: str) -> None:
        self.triggered.append(source)


class ErrorService(FakeNusantarumService):
    async def list_perfumes(self, **_: Any) -> PagedResult:
        raise NusantarumConfigurationError("Supabase credentials belum dikonfigurasi")


@pytest.fixture
def fake_service() -> FakeNusantarumService:
    service = FakeNusantarumService()
    app.dependency_overrides[get_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


async def _send_request(
    method: str,
    path: str,
    *,
    query_string: str = "",
    body: bytes = b"",
    headers: List[Tuple[bytes, bytes]] | None = None,
) -> Tuple[int, Dict[str, str], bytes]:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query_string.encode("ascii"),
        "headers": headers or [],
        "client": ("127.0.0.1", 0),
        "server": ("testserver", 80),
    }
    messages: List[Dict[str, Any]] = []

    async def receive() -> Dict[str, Any]:
        nonlocal body
        chunk = body
        body = b""
        return {"type": "http.request", "body": chunk, "more_body": False}

    async def send(message: Dict[str, Any]) -> None:
        messages.append(message)

    await app(scope, receive, send)

    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    raw_headers = next(m["headers"] for m in messages if m["type"] == "http.response.start")
    response_headers = {key.decode().lower(): value.decode() for key, value in raw_headers}
    body_bytes = b"".join(m["body"] for m in messages if m["type"] == "http.response.body")
    return status, response_headers, body_bytes


def test_index_page_renders_with_perfume_list(fake_service: FakeNusantarumService) -> None:
    status, headers, body = asyncio.run(_send_request("GET", "/nusantarum"))
    assert status == 200
    assert headers["content-type"].startswith("text/html")
    text = body.decode()
    assert "Hutan Senja" in text
    assert "Pusat Kurasi Parfum Lokal Indonesia" in text


def test_tab_endpoint_returns_partial(fake_service: FakeNusantarumService) -> None:
    status, headers, body = asyncio.run(_send_request("GET", "/nusantarum/tab/brand"))
    assert status == 200
    assert headers["content-type"].startswith("text/html")
    assert "Langit Senja" in body.decode()


def test_search_endpoint_returns_html(fake_service: FakeNusantarumService) -> None:
    status, headers, body = asyncio.run(
        _send_request("GET", "/nusantarum/search", query_string="q=senja")
    )
    assert status == 200
    assert headers["content-type"].startswith("text/html")
    assert "Senja Parfum" in body.decode()


def test_trigger_sync_records_source(fake_service: FakeNusantarumService) -> None:
    status, headers, body = asyncio.run(
        _send_request("POST", "/nusantarum/sync/marketplace")
    )
    assert status == 200
    assert json.loads(body)["status"] == "queued"
    assert fake_service.triggered == ["marketplace"]


def test_index_handles_configuration_error() -> None:
    app.dependency_overrides[get_service] = lambda: ErrorService()
    status, headers, body = asyncio.run(_send_request("GET", "/nusantarum"))
    assert status == 200
    assert "Supabase credentials" in body.decode()
    app.dependency_overrides.clear()
