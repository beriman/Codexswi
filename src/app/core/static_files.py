"""Optimized static file serving with caching headers."""

from starlette.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope, Receive, Send


class CachedStaticFiles(StaticFiles):
    """Static files middleware with aggressive caching for immutable assets."""
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Add cache headers to static file responses."""
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add cache headers for static assets
                # Assets with version query params are immutable
                if b"Cache-Control" not in headers:
                    # Cache for 1 year for versioned assets
                    headers[b"Cache-Control"] = b"public, max-age=31536000, immutable"
                
                # Add compression hint
                headers[b"Vary"] = b"Accept-Encoding"
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await super().__call__(scope, receive, send_wrapper)
