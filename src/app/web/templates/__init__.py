"""Template utilities for Jinja2 rendering."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

TEMPLATES_DIR = Path(__file__).parent

template_engine = Jinja2Templates(directory=str(TEMPLATES_DIR))

settings = get_settings()

template_engine.env.globals.update(
    app_name=settings.app_name,
    static_asset_version=settings.static_asset_version,
    static_asset_query=f"v={settings.static_asset_version}",
)
