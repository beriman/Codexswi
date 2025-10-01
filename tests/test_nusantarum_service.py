"""Unit tests for the Nusantarum service layer."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import pytest

from app.services.nusantarum_service import (
    NusantarumService,
    PerfumeListItem,
)


class DummyGateway:
    """In-memory gateway faking Supabase responses for the service tests."""

    def __init__(self) -> None:
        self.calls: List[Tuple[str, Sequence[Tuple[str, Any]]]] = []
        self.perfume_rows = [
            {
                "id": "pf-1",
                "name": "Hutan Senja",
                "slug": "hutan-senja",
                "brand_name": "Langit Senja",
                "brand_slug": "langit-senja",
                "brand_city": "Bandung",
                "brand_profile_username": "langit-senja",
                "perfumer_name": "Ayu Pratiwi",
                "perfumer_slug": "ayu-pratiwi",
                "perfumer_profile_username": "ayu-pratiwi",
                "hero_note": "Jasmine dan kayu cendana",
                "description": "Aroma nostalgia senja di hutan pinus.",
                "aroma_families": ["Floral", "Woody"],
                "price_reference": 450000,
                "price_currency": "IDR",
                "marketplace_price": 470000,
                "marketplace_status": "published",
                "marketplace_product_id": "prod-1",
                "base_image_url": "https://cdn.example.com/hutan-senja.jpg",
                "sync_source": "marketplace",
                "sync_status": "success",
                "synced_at": "2024-04-01T08:30:00+00:00",
                "updated_at": "2024-04-02T10:00:00+00:00",
                "marketplace_rating": 4.7,
            }
        ]
        self.brand_rows = [
            {
                "id": "brand-1",
                "name": "Langit Senja",
                "slug": "langit-senja",
                "origin_city": "Bandung",
                "active_perfume_count": 3,
                "nusantarum_status": "aktif",
                "brand_profile_username": "langit-senja",
                "last_perfume_synced_at": "2024-04-01T08:30:00+00:00",
            }
        ]
        self.perfumer_rows = [
            {
                "id": "pfmr-1",
                "slug": "ayu-pratiwi",
                "display_name": "Ayu Pratiwi",
                "city": "Bandung",
                "bio": "Perfumer indie dengan fokus aroma tropis dan flora nusantara yang kaya.",
                "signature_scent": "Tropical jasmine",
                "active_perfume_count": 2,
                "followers_count": 1200,
                "years_active": 5,
                "is_curated": True,
                "perfumer_profile_username": "ayu-pratiwi",
                "highlight_perfume": "Hutan Senja",
                "highlight_brand": "Langit Senja",
                "last_synced_at": "2024-04-02T10:00:00+00:00",
            }
        ]
        self.sync_logs = [
            {
                "source": "marketplace",
                "status": "success",
                "summary": "Synced",
                "run_at": "2024-04-02T11:00:00+00:00",
            }
        ]
        self.rpc_calls: List[str] = []

    async def fetch_directory(
        self,
        resource: str,
        *,
        page: int,
        page_size: int,
        filters: Iterable[Tuple[str, Any]] | None = None,
        order: str | None = None,
    ) -> Dict[str, Any]:
        self.calls.append((resource, tuple(filters or [])))
        data_map = {
            "nusantarum_perfume_directory": self.perfume_rows,
            "nusantarum_brand_directory": self.brand_rows,
            "nusantarum_perfumer_directory": self.perfumer_rows,
        }
        data = data_map.get(resource, [])
        return {"data": data, "total": len(data)}

    async def fetch_sync_logs(self, *, limit: int = 5) -> List[Dict[str, Any]]:
        return self.sync_logs[:limit]

    async def rpc(self, name: str, payload: Dict[str, Any] | None = None) -> Any:
        self.rpc_calls.append(name)
        return None


def test_list_perfumes_transforms_rows_and_caches() -> None:
    gateway = DummyGateway()
    service = NusantarumService(gateway=gateway, cache_ttl=60)

    result = asyncio.run(
        service.list_perfumes(families=["Floral"], city="Bandung", price_min=400000)
    )

    assert isinstance(result.items[0], PerfumeListItem)
    assert result.items[0].brand_profile_url == "/profile/langit-senja"
    assert result.items[0].marketplace_url == "/marketplace/products/prod-1"
    assert gateway.calls, "Gateway should have been called"

    # Second call with identical filters should hit the cache
    asyncio.run(service.list_perfumes(families=["Floral"], city="Bandung", price_min=400000))
    assert len(gateway.calls) == 1


def test_list_brands_and_perfumers_use_directory_views() -> None:
    gateway = DummyGateway()
    service = NusantarumService(gateway=gateway, cache_ttl=0)

    brand_page = asyncio.run(service.list_brands(city="Bandung"))
    perfumer_page = asyncio.run(service.list_perfumers())

    assert brand_page.items[0].name == "Langit Senja"
    assert perfumer_page.items[0].display_name == "Ayu Pratiwi"
    resources = {call[0] for call in gateway.calls}
    assert "nusantarum_brand_directory" in resources
    assert "nusantarum_perfumer_directory" in resources


def test_get_sync_status_and_trigger_sync_call_gateway() -> None:
    gateway = DummyGateway()
    service = NusantarumService(gateway=gateway)

    status = asyncio.run(service.get_sync_status())
    assert status[0].source == "marketplace"
    assert isinstance(status[0].run_at, datetime)

    asyncio.run(service.trigger_sync("marketplace"))
    assert gateway.rpc_calls == ["sync_marketplace_products"]


def test_search_combines_categories() -> None:
    gateway = DummyGateway()
    service = NusantarumService(gateway=gateway, cache_ttl=0)

    results = asyncio.run(service.search("senja"))

    assert "Hutan Senja" in results["perfumes"]
    assert "Langit Senja" in results["brands"]
    assert "Ayu Pratiwi" in results["perfumers"]
