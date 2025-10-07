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
from app.services.scheduler import start_scheduler, stop_scheduler
from app.api.routes import onboarding as onboarding_routes
from app.api.routes import profile as profile_routes
from app.api.routes import reports as reports_routes
from app.api.routes import root as root_routes
from app.api.routes import sambatan as sambatan_routes
from app.api.routes import brands as brand_routes
from app.api.routes import nusantarum as nusantarum_routes
from app.api.routes import cart as cart_routes
from app.api.routes import checkout as checkout_routes
from app.api.routes import products as products_routes
from app.api.routes import wallet as wallet_routes

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
    # Only mount if the directory exists (may not be available in serverless deployments)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    else:
        logger.warning(f"Static directory not found at {STATIC_DIR}, skipping mount")

    # Register routers for server-rendered pages and API endpoints.
    app.include_router(root_routes.router)
    app.include_router(brand_routes.router)
    app.include_router(reports_routes.router)
    app.include_router(onboarding_routes.router)
    app.include_router(sambatan_routes.router)
    app.include_router(products_routes.router)
    app.include_router(profile_routes.router)
    app.include_router(nusantarum_routes.router)
    app.include_router(cart_routes.router)
    app.include_router(checkout_routes.router)
    app.include_router(wallet_routes.router)
    from app.api.routes import auth as auth_routes
    from app.api.routes import moderation as moderation_routes
    from app.api.routes import team as team_routes

    app.include_router(auth_routes.router)
    app.include_router(moderation_routes.router)
    app.include_router(team_routes.router)

    # Expose the template engine on the app state for reuse by routers.
    app.state.templates = template_engine

    # Initialize Supabase client on startup
    @app.on_event("startup")
    async def startup():
        try:
            client = get_supabase_client()
            if client:
                app.state.supabase = client
                logger.info("Supabase client initialized successfully")
                
                # Start the Sambatan lifecycle scheduler
                # Skip scheduler in serverless environments (Vercel)
                import os
                is_vercel = os.getenv("VERCEL", "0") == "1"
                
                if not is_vercel:
                    try:
                        scheduler = start_scheduler(interval_minutes=5)
                        app.state.sambatan_scheduler = scheduler
                        app.state.scheduler_healthy = True
                        logger.info("Sambatan lifecycle scheduler started successfully")
                    except Exception as e:
                        logger.error(f"Failed to start Sambatan scheduler: {e}", exc_info=True)
                        app.state.scheduler_healthy = False
                        logger.warning(
                            "⚠️  Application running WITHOUT automated Sambatan lifecycle! "
                            "Manual triggering via API will still work."
                        )
                else:
                    logger.info("Running in Vercel serverless environment - scheduler disabled")
                    app.state.scheduler_healthy = False
            else:
                logger.warning("Supabase client not available - using fallback storage")
        except Exception as e:
            logger.error(f"Error during startup: {e}", exc_info=True)
            # Don't fail the startup, just log the error
            app.state.scheduler_healthy = False

    @app.on_event("shutdown")
    async def shutdown():
        # Stop the scheduler on application shutdown
        try:
            stop_scheduler()
            logger.info("Sambatan lifecycle scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping Sambatan scheduler: {e}")

    return app
