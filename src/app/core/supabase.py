"""Supabase client initialization and configuration."""

from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supabase import Client
else:
    try:
        from supabase import create_client, Client
        SUPABASE_AVAILABLE = True
    except ImportError:
        SUPABASE_AVAILABLE = False
        Client = Any  # type: ignore
        create_client = None  # type: ignore

from app.core.config import get_settings


class SupabaseError(Exception):
    """Raised when Supabase operations fail."""


@lru_cache
def get_supabase_client() -> Client | None:
    """Return a configured Supabase client or None if unavailable."""
    
    if not SUPABASE_AVAILABLE or create_client is None:
        return None
    
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )


def require_supabase() -> Client:
    """Return Supabase client or raise if not configured."""
    
    client = get_supabase_client()
    if client is None:
        raise SupabaseError(
            "Supabase is not configured. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY environment variables."
        )
    return client
