"""Application factory for the Sensasiwangi.id MVP."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.core.config import get_settings
from app.web.templates import template_engine
from app.api.routes import root as root_routes

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Basic CORS setup to simplify early integrations with Supabase and
    # front-end previews during the MVP stage.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static assets (CSS, JS, images) served by the Jinja2 templates.
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routers for server-rendered pages.
    app.include_router(root_routes.router)

    # Expose the template engine on the app state for reuse by routers.
    app.state.templates = template_engine

    return app
