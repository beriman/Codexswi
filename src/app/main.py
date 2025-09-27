"""Entry point for ASGI servers."""

from app.core.application import create_app

app = create_app()
