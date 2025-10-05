"""FastAPI dependencies for dependency injection."""

from typing import Optional
from fastapi import Depends, Request

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

from app.core.supabase import get_supabase_client


def get_db(request: Request) -> Optional[Client]:
    """Provide Supabase client to route handlers."""
    
    if hasattr(request.app.state, 'supabase'):
        return request.app.state.supabase
    
    # Fallback to creating new client
    client = get_supabase_client()
    if not client:
        raise RuntimeError("Supabase client not initialized")
    return client
