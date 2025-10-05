"""Application factory for the Sensasiwangi.id MVP."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.session import InMemorySessionMiddleware
from app.core.supabase import get_supabase_client
from app.core.rate_limit import limiter
from app.web.templates import template_engine
from app.api.routes import onboarding as onboarding_routes
from app.api.routes import profile as profile_routes
from app.api.routes import reports as reports_routes
from app.api.routes import root as root_routes
from app.api.routes import sambatan as sambatan_routes
from app.api.routes import brands as brand_routes
from app.api.routes import nusantarum as nusantarum_routes
from app.api.routes import cart as cart_routes
from app.api.routes import checkout as checkout_routes

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Add rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

    # Mount static assets (CSS, JS, images) served by the Jinja2 templates.
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routers for server-rendered pages and API endpoints.
    app.include_router(root_routes.router)
    app.include_router(brand_routes.router)
    app.include_router(reports_routes.router)
    app.include_router(onboarding_routes.router)
    app.include_router(sambatan_routes.router)
    app.include_router(profile_routes.router)
    app.include_router(nusantarum_routes.router)
    app.include_router(cart_routes.router)
    app.include_router(checkout_routes.router)
    from app.api.routes import auth as auth_routes

    app.include_router(auth_routes.router)

    # Expose the template engine on the app state for reuse by routers.
    app.state.templates = template_engine

    # Initialize Supabase client on startup
    @app.on_event("startup")
    async def startup():
        client = get_supabase_client()
        if client:
            app.state.supabase = client
            logger.info("Supabase client initialized successfully")
        else:
            logger.warning("Supabase client not available - using fallback storage")

    return app
