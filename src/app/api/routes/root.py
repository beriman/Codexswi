"""Landing page routes for the MVP."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import get_settings

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request) -> HTMLResponse:
    """Render the marketplace landing page placeholder."""

    settings = get_settings()
    templates = request.app.state.templates
    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
    }
    return templates.TemplateResponse("index.html", context)
