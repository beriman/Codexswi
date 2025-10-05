"""Template utilities for Jinja2 rendering."""

import logging
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent

# Initialize template engine with error handling
try:
    template_engine = Jinja2Templates(directory=str(TEMPLATES_DIR))
    logger.info(f"Template engine initialized with directory: {TEMPLATES_DIR}")
    
    settings = get_settings()
    
    template_engine.env.globals.update(
        app_name=settings.app_name,
        static_asset_version=settings.static_asset_version,
        static_asset_query=f"v={settings.static_asset_version}",
    )
except Exception as e:
    logger.error(f"Failed to initialize template engine: {e}", exc_info=True)
    # Create a minimal template engine as fallback
    import tempfile
    fallback_dir = tempfile.mkdtemp()
    template_engine = Jinja2Templates(directory=fallback_dir)
    logger.warning(f"Using fallback template directory: {fallback_dir}")
