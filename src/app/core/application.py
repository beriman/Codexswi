"""Application factory for the Sensasiwangi.id MVP."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import get_settings
from app.core.session import InMemorySessionMiddleware
from app.core.static_files import CachedStaticFiles
from app.web.templates import template_engine
from app.api.routes import onboarding as onboarding_routes
from app.api.routes import profile as profile_routes
from app.api.routes import reports as reports_routes
from app.api.routes import root as root_routes
from app.api.routes import sambatan as sambatan_routes
from app.api.routes import brands as brand_routes
from app.api.routes import nusantarum as nusantarum_routes

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Add GZip compression for better performance
    if settings.enable_compression:
        app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

    app.add_middleware(
        InMemorySessionMiddleware,
        max_age=60 * 60 * 24 * 30,
        same_site="lax",
    )

    # Basic CORS setup to simplify early integrations with Supabase and
    # front-end previews during the MVP stage.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static assets (CSS, JS, images) with optimized caching.
    app.mount("/static", CachedStaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routers for server-rendered pages and API endpoints.
    app.include_router(root_routes.router)
    app.include_router(brand_routes.router)
    app.include_router(reports_routes.router)
    app.include_router(onboarding_routes.router)
    app.include_router(sambatan_routes.router)
    app.include_router(profile_routes.router)
    app.include_router(nusantarum_routes.router)
    from app.api.routes import auth as auth_routes

    app.include_router(auth_routes.router)

    # Expose the template engine on the app state for reuse by routers.
    app.state.templates = template_engine

    return app
