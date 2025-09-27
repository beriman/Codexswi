"""Template utilities for Jinja2 rendering."""

from pathlib import Path
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent

template_engine = Jinja2Templates(directory=str(TEMPLATES_DIR))
