"""FastAPI entrypoint for deployment platforms like Vercel."""
from __future__ import annotations

import sys
import logging
import traceback
from pathlib import Path

# Configure logging early to capture any initialization errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure the "src" directory is on the import path so that the FastAPI application
# package can be imported when this file is executed by hosting platforms.
# This file is in /api/index.py, so parent is /api and parent.parent is the root
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

logger.info(f"ROOT_DIR: {ROOT_DIR}")
logger.info(f"SRC_DIR: {SRC_DIR}")
logger.info(f"SRC_DIR exists: {SRC_DIR.exists()}")

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    logger.info(f"Added {SRC_DIR} to sys.path")

# Create a fallback app in case the main app fails to load
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = None

try:
    logger.info("Attempting to import application...")
    from app.main import app as main_app  # noqa: E402
    app = main_app
    logger.info("✓ FastAPI application loaded successfully")
except Exception as e:
    logger.error(f"✗ Failed to load FastAPI application: {e}")
    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    # Create a minimal fallback app that at least responds
    logger.warning("Creating fallback application")
    app = FastAPI(title="Sensasiwangi.id - Error Mode")
    
    @app.get("/")
    async def fallback_root():
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Application failed to initialize",
                "error": str(e),
                "instructions": "Please check environment variables and Vercel logs"
            }
        )
    
    @app.get("/health")
    async def fallback_health():
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

# Add a health check endpoint if it doesn't exist
if app:
    try:
        if not any(hasattr(route, 'path') and route.path == "/health" for route in app.routes):
            @app.get("/health")
            async def health_check():
                return {"status": "healthy", "service": "sensasiwangi.id"}
    except AttributeError:
        pass

# Vercel serverless function handler
# This is required for Vercel to properly invoke the ASGI app
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    logger.info("✓ Mangum handler created successfully")
except ImportError:
    logger.warning("Mangum not available, using app directly")
    handler = app

__all__ = ["app", "handler"]
