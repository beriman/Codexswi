"""FastAPI entrypoint for deployment platforms like Vercel.

This is the legacy entry point kept for backwards compatibility.
For Vercel deployments, api/index.py is used instead.
"""
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
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

logger.info(f"ROOT_DIR: {ROOT_DIR}")
logger.info(f"SRC_DIR: {SRC_DIR}")

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    logger.info(f"Added {SRC_DIR} to sys.path")

try:
    from app.main import app  # noqa: E402
    logger.info("✓ FastAPI application loaded successfully")
except Exception as e:
    logger.error(f"✗ Failed to load FastAPI application: {e}")
    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    # Re-raise the exception so it's visible
    raise

__all__ = ["app"]
