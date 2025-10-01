"""Routing module for the Nusantarum directory experience."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.nusantarum_service import (
    NusantarumConfigurationError,
    NusantarumError,
    NusantarumService,
    nusantarum_service,
)


router = APIRouter(prefix="/nusantarum", tags=["nusantarum"])


def get_service() -> NusantarumService:
    return nusantarum_service


async def _load_perfume_tab(
    service: NusantarumService,
    *,
    page: int,
    page_size: int,
    families: List[str],
    city: str | None,
    price_min: float | None,
    price_max: float | None,
    verified: bool,
    sort: str | None,
    direction: str | None,
):
    return await service.list_perfumes(
        page=page,
        page_size=page_size,
        families=families,
        city=city,
        price_min=price_min,
        price_max=price_max,
        verified_only=verified,
        sort=sort,
        direction=direction,
    )


async def _load_brand_tab(
    service: NusantarumService,
    *,
    page: int,
    page_size: int,
    families: List[str],
    city: str | None,
    price_min: float | None,
    price_max: float | None,
    verified: bool,
    sort: str | None,
    direction: str | None,
):
    del families, price_min, price_max
    del sort, direction
    return await service.list_brands(page=page, page_size=page_size, city=city, verified_only=verified)


async def _load_perfumer_tab(
    service: NusantarumService,
    *,
    page: int,
    page_size: int,
    families: List[str],
    city: str | None,
    price_min: float | None,
    price_max: float | None,
    verified: bool,
    sort: str | None,
    direction: str | None,
):
    del families, city, price_min, price_max
    del sort, direction
    return await service.list_perfumers(page=page, page_size=page_size, verified_only=verified)


TAB_LOADERS: Dict[str, Tuple[str, Callable[..., Any]]] = {
    "parfum": ("components/nusantarum/perfume-list.html", _load_perfume_tab),
    "brand": ("components/nusantarum/brand-list.html", _load_brand_tab),
    "perfumer": ("components/nusantarum/perfumer-list.html", _load_perfumer_tab),
}


@router.get("", response_class=HTMLResponse, name="nusantarum:index")
async def nusantarum_index(
    request: Request,
    service: NusantarumService = Depends(get_service),
    families: List[str] = Query(default_factory=list),
    city: str | None = Query(default=None),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    verified: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    tab: str = Query(default="parfum"),
    sort: str | None = Query(default=None),
    direction: str | None = Query(default=None),
) -> HTMLResponse:
    templates = request.app.state.templates
    tab_slug = tab.lower()
    if tab_slug not in TAB_LOADERS:
        raise HTTPException(status_code=404, detail="Tab tidak ditemukan")

    filters = {
        "families": families,
        "city": city,
        "price_min": price_min,
        "price_max": price_max,
        "verified": verified,
    }

    active_template, active_loader = TAB_LOADERS[tab_slug]

    normalized_sort = None
    normalized_direction = None
    if tab_slug == "parfum":
        normalized_sort, normalized_direction, _ = NusantarumService.normalize_perfume_sort(sort, direction)

    load_kwargs = {
        "page": page,
        "page_size": page_size,
        "families": families,
        "city": city,
        "price_min": price_min,
        "price_max": price_max,
        "verified": verified,
        "sort": normalized_sort if tab_slug == "parfum" else None,
        "direction": normalized_direction if tab_slug == "parfum" else None,
    }

    try:
        active_page = await active_loader(service, **load_kwargs)
        error_message = None
    except NusantarumConfigurationError as exc:
        active_page = None
        error_message = str(exc)

    async def _load_total(slug: str, loader: Callable[..., Any]) -> tuple[str, int]:
        if slug == tab_slug:
            total = active_page.total if active_page else 0
            return slug, total
        try:
            snapshot = await loader(
                service,
                page=1,
                page_size=1,
                families=families,
                city=city,
                price_min=price_min,
                price_max=price_max,
                verified=verified,
                sort=normalized_sort if slug == "parfum" else None,
                direction=normalized_direction if slug == "parfum" else None,
            )
            return slug, snapshot.total
        except NusantarumConfigurationError:
            return slug, 0

    totals_results = await asyncio.gather(
        *[
            _load_total(slug, loader)
            for slug, (_, loader) in TAB_LOADERS.items()
        ],
        return_exceptions=False,
    )

    slug_to_total_key = {
        "parfum": "perfumes",
        "brand": "brands",
        "perfumer": "perfumers",
    }
    directory_totals = {value: 0 for value in slug_to_total_key.values()}
    for slug, total in totals_results:
        directory_totals[slug_to_total_key[slug]] = total

    try:
        sync_status = await service.get_sync_status()
    except NusantarumConfigurationError:
        sync_status = []

    context = {
        "title": "Nusantarum Directory",
        "filters": filters,
        "tab_page": active_page,
        "tab_template": active_template,
        "sync_status": sync_status,
        "error_message": error_message,
        "active_tab": tab_slug,
        "directory_totals": directory_totals,
        "sort": normalized_sort if tab_slug == "parfum" else None,
        "direction": normalized_direction if tab_slug == "parfum" else None,
    }
    return templates.TemplateResponse(request, "pages/nusantarum/index.html", context)


@router.get("/tab/{slug}", response_class=HTMLResponse, name="nusantarum:tab")
async def nusantarum_tab(
    slug: str,
    request: Request,
    service: NusantarumService = Depends(get_service),
    families: List[str] = Query(default_factory=list),
    city: str | None = Query(default=None),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    verified: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    sort: str | None = Query(default=None),
    direction: str | None = Query(default=None),
) -> HTMLResponse:
    slug = slug.lower()
    if slug not in TAB_LOADERS:
        raise HTTPException(status_code=404, detail="Tab tidak ditemukan")

    template_name, loader = TAB_LOADERS[slug]
    templates = request.app.state.templates

    normalized_sort = None
    normalized_direction = None
    if slug == "parfum":
        normalized_sort, normalized_direction, _ = NusantarumService.normalize_perfume_sort(sort, direction)

    try:
        page_data = await loader(
            service,
            page=page,
            page_size=page_size,
            families=families,
            city=city,
            price_min=price_min,
            price_max=price_max,
            verified=verified,
            sort=normalized_sort if slug == "parfum" else None,
            direction=normalized_direction if slug == "parfum" else None,
        )
        error_message = None
    except NusantarumConfigurationError as exc:
        page_data = None
        error_message = str(exc)

    context = {
        "page": page_data,
        "error_message": error_message,
        "filters": {
            "families": families,
            "city": city,
            "price_min": price_min,
            "price_max": price_max,
            "verified": verified,
        },
        "active_tab": slug,
        "sort": normalized_sort if slug == "parfum" else None,
        "direction": normalized_direction if slug == "parfum" else None,
    }
    return templates.TemplateResponse(request, template_name, context)


@router.get("/search", response_class=HTMLResponse, name="nusantarum:search")
async def nusantarum_search(
    request: Request,
    query: str = Query(alias="q"),
    service: NusantarumService = Depends(get_service),
) -> HTMLResponse:
    templates = request.app.state.templates
    try:
        results = await service.search(query)
    except NusantarumConfigurationError as exc:
        context = {
            "results": {"perfumes": [], "brands": [], "perfumers": []},
            "error_message": str(exc),
        }
        return templates.TemplateResponse(
            request,
            "components/nusantarum/search-results.html",
            context,
        )

    context = {"results": results, "error_message": None}
    return templates.TemplateResponse(
        request,
        "components/nusantarum/search-results.html",
        context,
    )


@router.post("/sync/{source}", response_class=JSONResponse, name="nusantarum:trigger-sync")
async def trigger_sync(
    source: str,
    service: NusantarumService = Depends(get_service),
) -> JSONResponse:
    source = source.lower()
    if source not in {"marketplace", "profiles"}:
        raise HTTPException(status_code=400, detail="Sumber sinkronisasi tidak dikenal")

    try:
        await service.trigger_sync(source)
    except NusantarumConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except NusantarumError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse({"status": "queued", "source": source})
