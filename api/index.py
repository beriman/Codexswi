"""FastAPI entrypoint for deployment platforms like Vercel."""
from __future__ import annotations

import sys
import logging
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
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from app.main import app  # noqa: E402
    logger.info("FastAPI application loaded successfully")
except Exception as e:
    logger.error(f"Failed to load FastAPI application: {e}", exc_info=True)
    # Re-raise the exception so Vercel logs it properly
    raise

__all__ = ["app"]
