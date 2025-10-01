"""Service layer for Nusantarum directory integration with Supabase."""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence, Tuple, TypedDict

try:  # pragma: no cover - gracefully handle missing optional dependency
    import httpx
except ModuleNotFoundError:  # pragma: no cover - environment without httpx
    class _HttpxStub:  # type: ignore[override]
        class HTTPStatusError(RuntimeError):
            pass

        class AsyncClient:  # noqa: D401 - simple stub
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise RuntimeError(
                    "httpx package is required for Supabase integration. "
                    "Install httpx or provide a custom gateway."
                )

    httpx = _HttpxStub()  # type: ignore[assignment]

from app.core.config import get_settings


class NusantarumError(Exception):
    """Base error for Nusantarum operations."""


class NusantarumConfigurationError(NusantarumError):
    """Raised when Supabase credentials are not configured."""


class NusantarumGatewayError(NusantarumError):
    """Raised when Supabase responds with an unexpected error."""


class GatewayResult(TypedDict, total=False):
    data: List[Dict[str, Any]]
    total: Optional[int]


class NusantarumGateway(Protocol):
    """Protocol describing the Supabase gateway used by the service."""

    async def fetch_directory(
        self,
        resource: str,
        *,
        page: int,
        page_size: int,
        filters: Iterable[Tuple[str, Any]] | None = None,
        order: str | None = None,
    ) -> GatewayResult:
        ...

    async def fetch_sync_logs(self, *, limit: int = 5) -> List[Dict[str, Any]]:
        ...

    async def rpc(self, name: str, payload: Dict[str, Any] | None = None) -> Any:
        ...


@dataclass(slots=True)
class PerfumeListItem:
    """Representation of a parfum item rendered on the Nusantarum page."""

    id: str
    name: str
    slug: str
    brand_name: str
    brand_slug: str
    brand_city: Optional[str]
    brand_profile_username: Optional[str]
    perfumer_name: Optional[str]
    perfumer_slug: Optional[str]
    perfumer_profile_username: Optional[str]
    hero_note: Optional[str]
    description: Optional[str]
    aroma_families: List[str]
    price_reference: Optional[float]
    price_currency: str
    marketplace_price: Optional[float]
    marketplace_status: Optional[str]
    marketplace_product_id: Optional[str]
    base_image_url: Optional[str]
    sync_source: str
    sync_status: Optional[str]
    synced_at: Optional[datetime]
    updated_at: Optional[datetime]
    marketplace_rating: Optional[float]

    @property
    def marketplace_url(self) -> Optional[str]:
        if self.marketplace_product_id:
            return f"/marketplace/products/{self.marketplace_product_id}"
        return None

    @property
    def brand_profile_url(self) -> Optional[str]:
        if self.brand_profile_username:
            return f"/profile/{self.brand_profile_username}"
        return None

    @property
    def perfumer_profile_url(self) -> Optional[str]:
        if self.perfumer_profile_username:
            return f"/profile/{self.perfumer_profile_username}"
        return None


@dataclass(slots=True)
class BrandListItem:
    id: str
    name: str
    slug: str
    origin_city: Optional[str]
    active_perfume_count: int
    nusantarum_status: Optional[str]
    brand_profile_username: Optional[str]
    last_perfume_synced_at: Optional[datetime]

    @property
    def profile_url(self) -> Optional[str]:
        if self.brand_profile_username:
            return f"/profile/{self.brand_profile_username}"
        return None


@dataclass(slots=True)
class PerfumerListItem:
    id: str
    display_name: str
    slug: str
    city: Optional[str]
    bio_preview: Optional[str]
    signature_scent: Optional[str]
    active_perfume_count: int
    followers_count: int
    years_active: Optional[int]
    is_curated: bool
    perfumer_profile_username: Optional[str]
    highlight_perfume: Optional[str]
    highlight_brand: Optional[str]
    last_synced_at: Optional[datetime]

    @property
    def profile_url(self) -> Optional[str]:
        if self.perfumer_profile_username:
            return f"/profile/{self.perfumer_profile_username}"
        return None


@dataclass(slots=True)
class SyncLog:
    source: str
    status: str
    summary: Optional[str]
    run_at: datetime


@dataclass(slots=True)
class PagedResult:
    items: List[Any]
    total: Optional[int]
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        if not self.total:
            return 1
        return max(1, math.ceil(self.total / self.page_size))


class HttpSupabaseGateway:
    """HTTP implementation of the Supabase gateway using PostgREST endpoints."""

    def __init__(self, *, base_url: str, api_key: str, schema: str = "public", timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/") + "/rest/v1"
        self._schema = schema
        self._timeout = timeout
        self._headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Accept-Profile": schema,
        }

    async def fetch_directory(
        self,
        resource: str,
        *,
        page: int,
        page_size: int,
        filters: Iterable[Tuple[str, Any]] | None = None,
        order: str | None = None,
    ) -> GatewayResult:
        params: List[Tuple[str, Any]] = [("select", "*")]
        if filters:
            params.extend(list(filters))
        if order:
            params.append(("order", order))

        offset = (page - 1) * page_size
        headers = {**self._headers, "Prefer": "count=exact"}

        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get(
                f"/{resource}",
                headers=headers,
                params=[("limit", page_size), ("offset", offset), *params],
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure
            raise NusantarumGatewayError(str(exc)) from exc

        data = response.json()
        total = self._parse_total(response.headers.get("content-range"))
        return {"data": data, "total": total}

    async def fetch_sync_logs(self, *, limit: int = 5) -> List[Dict[str, Any]]:
        params = {
            "order": "run_at.desc",
            "limit": limit,
            "select": "*",
        }
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.get("/nusantarum_sync_logs", headers=self._headers, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure
            raise NusantarumGatewayError(str(exc)) from exc
        return response.json()

    async def rpc(self, name: str, payload: Dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            response = await client.post(
                f"/rpc/{name}",
                headers=self._headers,
                json=payload or {},
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure
            raise NusantarumGatewayError(str(exc)) from exc
        if response.content:
            return response.json()
        return None

    @staticmethod
    def _parse_total(content_range: Optional[str]) -> Optional[int]:
        if not content_range:
            return None
        try:
            _, total = content_range.split("/")
            if total == "*":
                return None
            return int(total)
        except ValueError:
            return None


class _CacheEntry(TypedDict):
    expires_at: float
    value: PagedResult


class NusantarumService:
    """Facade providing cached access to Nusantarum directory data."""

    def __init__(
        self,
        gateway: NusantarumGateway | None = None,
        *,
        cache_ttl: float = 30.0,
    ) -> None:
        self._gateway = gateway
        self._cache_ttl = cache_ttl
        self._cache: Dict[Tuple[str, Tuple[Any, ...]], _CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _ensure_gateway(self) -> NusantarumGateway:
        if self._gateway is not None:
            return self._gateway
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise NusantarumConfigurationError(
                "Supabase credentials belum dikonfigurasi untuk Nusantarum."
            )
        self._gateway = HttpSupabaseGateway(
            base_url=settings.supabase_url,
            api_key=settings.supabase_service_role_key or settings.supabase_anon_key,
        )
        return self._gateway

    @staticmethod
    def normalize_perfume_sort(
        sort: str | None,
        direction: str | None,
    ) -> tuple[str, str, str]:
        """Validate perfume sort inputs and return normalized values.

        Parameters
        ----------
        sort:
            Requested sort key from the client. Supports ``synced_at`` (default),
            ``name``, ``brand``, and ``updated_at``.
        direction:
            Requested direction which can be ``asc`` or ``desc``.

        Returns
        -------
        tuple[str, str, str]
            A tuple of ``(normalized_sort, normalized_direction, order_clause)``
            ready to be passed to PostgREST.
        """

        valid_sorts: Dict[str, tuple[str, str, bool]] = {
            "synced_at": ("synced_at", "desc", True),
            "name": ("name", "asc", False),
            "brand": ("brand_name", "asc", False),
            "updated_at": ("updated_at", "desc", True),
        }

        requested_sort = (sort or "").lower()
        column, default_direction, nulls_last = valid_sorts.get(
            requested_sort, valid_sorts["synced_at"]
        )
        normalized_sort = requested_sort if requested_sort in valid_sorts else "synced_at"

        normalized_direction = (direction or "").lower()
        if normalized_direction not in {"asc", "desc"}:
            normalized_direction = default_direction

        order_clause = f"{column}.{normalized_direction}"
        if nulls_last:
            order_clause = f"{order_clause},nullslast"

        return normalized_sort, normalized_direction, order_clause

    async def list_perfumes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        families: Iterable[str] | None = None,
        city: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        verified_only: bool = True,
        sort: str | None = None,
        direction: str | None = None,
    ) -> PagedResult:
        filters: List[Tuple[str, Any]] = []
        if verified_only:
            filters.append(("brand_is_verified", "eq.true"))
        if families:
            filters.append(("aroma_families", "ov.{" + ",".join(families) + "}"))
        if city:
            filters.append(("brand_city", f"ilike.*{city}*"))
        if price_min is not None:
            filters.append(("marketplace_price", f"gte.{price_min}"))
        if price_max is not None:
            filters.append(("marketplace_price", f"lte.{price_max}"))

        _, _, order_clause = self.normalize_perfume_sort(sort, direction)

        payload = await self._fetch_with_cache(
            "perfumes",
            filters,
            page,
            page_size,
            order=order_clause,
        )
        items = [self._build_perfume(item) for item in payload.items]
        return PagedResult(items=items, total=payload.total, page=page, page_size=page_size)

    async def list_brands(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        city: str | None = None,
        verified_only: bool = True,
    ) -> PagedResult:
        filters: List[Tuple[str, Any]] = []
        if verified_only:
            filters.append(("is_verified", "eq.true"))
        if city:
            filters.append(("origin_city", f"ilike.*{city}*"))

        payload = await self._fetch_with_cache(
            "brands",
            filters,
            page,
            page_size,
            resource="nusantarum_brand_directory",
            order="name.asc",
        )
        items = [self._build_brand(item) for item in payload.items]
        return PagedResult(items=items, total=payload.total, page=page, page_size=page_size)

    async def list_perfumers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        verified_only: bool = True,
    ) -> PagedResult:
        filters: List[Tuple[str, Any]] = []
        if verified_only:
            filters.append(("is_verified", "eq.true"))

        payload = await self._fetch_with_cache(
            "perfumers",
            filters,
            page,
            page_size,
            resource="nusantarum_perfumer_directory",
            order="display_name.asc",
        )
        items = [self._build_perfumer(item) for item in payload.items]
        return PagedResult(items=items, total=payload.total, page=page, page_size=page_size)

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> Dict[str, List[str]]:
        q = query.strip()
        if not q:
            return {"perfumes": [], "brands": [], "perfumers": []}

        filters = [("name", f"ilike.*{q}*")]
        perfume_results = await self._fetch_with_cache(
            "perfumes-search",
            filters,
            1,
            limit,
            resource="nusantarum_perfume_directory",
            order="name.asc",
        )
        brand_results = await self._fetch_with_cache(
            "brands-search",
            [("name", f"ilike.*{q}*")],
            1,
            limit,
            resource="nusantarum_brand_directory",
            order="name.asc",
        )
        perfumer_results = await self._fetch_with_cache(
            "perfumers-search",
            [("display_name", f"ilike.*{q}*")],
            1,
            limit,
            resource="nusantarum_perfumer_directory",
            order="display_name.asc",
        )
        return {
            "perfumes": [item["name"] for item in perfume_results.items],
            "brands": [item["name"] for item in brand_results.items],
            "perfumers": [item["display_name"] for item in perfumer_results.items],
        }

    async def get_sync_status(self) -> List[SyncLog]:
        gateway = self._ensure_gateway()
        rows = await gateway.fetch_sync_logs(limit=5)
        status: List[SyncLog] = []
        for row in rows:
            try:
                run_at = datetime.fromisoformat(row["run_at"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                continue
            status.append(
                SyncLog(
                    source=row.get("source", "unknown"),
                    status=row.get("status", "unknown"),
                    summary=row.get("summary"),
                    run_at=run_at,
                )
            )
        return status

    async def trigger_sync(self, source: str) -> None:
        gateway = self._ensure_gateway()
        if source == "marketplace":
            await gateway.rpc("sync_marketplace_products")
        elif source == "profiles":
            await gateway.rpc("sync_nusantarum_profiles")
        else:  # pragma: no cover - defensive programming
            raise NusantarumError(f"Unknown sync source: {source}")

    async def _fetch_with_cache(
        self,
        cache_key: str,
        filters: Sequence[Tuple[str, Any]],
        page: int,
        page_size: int,
        *,
        resource: str = "nusantarum_perfume_directory",
        order: str | None = None,
    ) -> PagedResult:
        gateway = self._ensure_gateway()
        normalized_filters = tuple(sorted(filters))
        key = (cache_key, normalized_filters, page, page_size, resource, order)
        now = time.monotonic()

        entry = self._cache.get(key)
        if entry and entry["expires_at"] > now:
            return entry["value"]

        async with self._lock:
            entry = self._cache.get(key)
            if entry and entry["expires_at"] > now:
                return entry["value"]

            result = await gateway.fetch_directory(
                resource,
                page=page,
                page_size=page_size,
                filters=filters,
                order=order,
            )
            paged = PagedResult(
                items=result.get("data", []),
                total=result.get("total"),
                page=page,
                page_size=page_size,
            )
            self._cache[key] = {"expires_at": now + self._cache_ttl, "value": paged}
            return paged

    @staticmethod
    def _build_perfume(row: Dict[str, Any]) -> PerfumeListItem:
        return PerfumeListItem(
            id=str(row.get("id")),
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            brand_name=row.get("brand_name", ""),
            brand_slug=row.get("brand_slug", ""),
            brand_city=row.get("brand_city"),
            brand_profile_username=row.get("brand_profile_username"),
            perfumer_name=row.get("perfumer_name"),
            perfumer_slug=row.get("perfumer_slug"),
            perfumer_profile_username=row.get("perfumer_profile_username"),
            hero_note=row.get("hero_note"),
            description=row.get("description"),
            aroma_families=list(row.get("aroma_families") or []),
            price_reference=row.get("price_reference"),
            price_currency=row.get("price_currency", "IDR"),
            marketplace_price=row.get("marketplace_price"),
            marketplace_status=row.get("marketplace_status"),
            marketplace_product_id=row.get("marketplace_product_id"),
            base_image_url=row.get("base_image_url"),
            sync_source=row.get("sync_source", "manual"),
            sync_status=row.get("sync_status"),
            synced_at=_parse_datetime(row.get("synced_at")),
            updated_at=_parse_datetime(row.get("updated_at")),
            marketplace_rating=row.get("marketplace_rating"),
        )

    @staticmethod
    def _build_brand(row: Dict[str, Any]) -> BrandListItem:
        return BrandListItem(
            id=str(row.get("id")),
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            origin_city=row.get("origin_city"),
            active_perfume_count=int(row.get("active_perfume_count") or 0),
            nusantarum_status=row.get("nusantarum_status"),
            brand_profile_username=row.get("brand_profile_username"),
            last_perfume_synced_at=_parse_datetime(row.get("last_perfume_synced_at")),
        )

    @staticmethod
    def _build_perfumer(row: Dict[str, Any]) -> PerfumerListItem:
        city = row.get("city") or row.get("origin_city") or row.get("base_city")
        bio_source = row.get("bio") or row.get("biography")
        bio_preview = _truncate_text(bio_source)
        followers_raw = (
            row.get("followers_count")
            or row.get("follower_count")
            or row.get("followers")
            or 0
        )
        years_active_raw = row.get("years_active") or row.get("active_years")
        try:
            years_active = int(years_active_raw) if years_active_raw is not None else None
        except (TypeError, ValueError):
            years_active = None
        try:
            followers_count = int(followers_raw)
        except (TypeError, ValueError):
            followers_count = 0

        return PerfumerListItem(
            id=str(row.get("id")),
            display_name=row.get("display_name", ""),
            slug=row.get("slug", ""),
            city=city,
            bio_preview=bio_preview,
            signature_scent=row.get("signature_scent"),
            active_perfume_count=int(row.get("active_perfume_count") or 0),
            followers_count=followers_count,
            years_active=years_active,
            is_curated=bool(row.get("is_curated") or row.get("curated")),
            perfumer_profile_username=row.get("perfumer_profile_username"),
            highlight_perfume=row.get("highlight_perfume"),
            highlight_brand=row.get("highlight_brand"),
            last_synced_at=_parse_datetime(row.get("last_synced_at")),
        )


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _truncate_text(value: Any, *, limit: int = 140) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip()
    if len(text) <= limit:
        return text or None
    truncated = text[: limit - 1].rstrip()
    return f"{truncated}…"


nusantarum_service = NusantarumService()
"""Default singleton service instance used by routers and tests."""
