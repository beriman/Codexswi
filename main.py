"""FastAPI entrypoint for deployment platforms like Vercel."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the "src" directory is on the import path so that the FastAPI application
# package can be imported when this file is executed by hosting platforms.
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.main import app  # noqa: E402

__all__ = ["app"]
