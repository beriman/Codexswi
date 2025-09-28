"""Routes for the brand storefront experience."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.services.brands import BrandNotFound, brand_service


router = APIRouter()


@router.get("/brands/{slug}", response_class=HTMLResponse)
async def read_brand(request: Request, slug: str) -> HTMLResponse:
    """Render the public brand page with collaboration summary."""

    templates = request.app.state.templates
    settings = get_settings()

    try:
        brand = brand_service.get_brand(slug)
    except BrandNotFound as exc:  # pragma: no cover - handled via exception mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": brand.name,
        "brand": brand,
    }
    return templates.TemplateResponse("pages/brand/detail.html", context)


@router.get("/brands", response_class=HTMLResponse)
async def list_brands(request: Request) -> HTMLResponse:
    """Simple directory view to help merchant explore brand pages."""

    templates = request.app.state.templates
    settings = get_settings()
    brands = list(brand_service.list_brands())

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Brand Partner",
        "brands": brands,
    }
    return templates.TemplateResponse("pages/brand/index.html", context)

