"""Application factory for the Sensasiwangi.id MVP."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.session import InMemorySessionMiddleware
from app.core.supabase import get_supabase_client, check_supabase_connection
from app.web.templates import template_engine
from app.api.routes import onboarding as onboarding_routes
from app.api.routes import profile as profile_routes
from app.api.routes import reports as reports_routes
from app.api.routes import root as root_routes
from app.api.routes import sambatan as sambatan_routes
from app.api.routes import brands as brand_routes
from app.api.routes import nusantarum as nusantarum_routes

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    # Application lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services and connections on application startup."""
        
        logger.info(f"Starting {settings.app_name} ({settings.environment})")
        
        # Initialize Supabase client
        client = get_supabase_client()
        if client:
            app.state.supabase = client
            logger.info("✓ Supabase client initialized successfully")
            
            # Check connection health
            if check_supabase_connection():
                logger.info("✓ Supabase connection healthy")
            else:
                logger.warning("⚠ Supabase connection check failed")
        else:
            logger.warning(
                "⚠ Supabase client not available - using fallback storage. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to enable."
            )
        
        logger.info(f"Application startup complete")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup resources on application shutdown."""
        
        logger.info(f"Shutting down {settings.app_name}")
        
        # Cleanup Supabase client if needed
        if hasattr(app.state, 'supabase'):
            # Supabase client cleanup (if needed in future)
            pass
        
        logger.info("Application shutdown complete")

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
    from app.api.routes import auth as auth_routes

    app.include_router(auth_routes.router)

    # Expose the template engine on the app state for reuse by routers.
    app.state.templates = template_engine

    return app
