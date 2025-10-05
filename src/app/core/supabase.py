"""Supabase client initialization and configuration.

This module provides a centralized Supabase client factory that can be used
throughout the application. It handles connection pooling, error handling,
and graceful fallback when Supabase is not configured.

Usage:
    from app.core.supabase import get_supabase_client, require_supabase
    
    # Optional client (returns None if not configured)
    client = get_supabase_client()
    if client:
        result = client.table('products').select('*').execute()
    
    # Required client (raises error if not configured)
    client = require_supabase()
    result = client.table('products').select('*').execute()
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Try to import supabase, but don't fail if it's not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # type: ignore[misc,assignment]
    logger.warning(
        "supabase-py package not installed. "
        "Install with: pip install supabase"
    )


class SupabaseError(Exception):
    """Raised when Supabase operations fail."""


class SupabaseNotConfigured(SupabaseError):
    """Raised when Supabase credentials are missing."""


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional[Client]:  # type: ignore[valid-type]
    """Return a configured Supabase client or None if unavailable.
    
    This function is cached to ensure we only create one client instance
    per application lifecycle.
    
    Returns:
        Supabase client if properly configured, None otherwise.
    
    Example:
        >>> client = get_supabase_client()
        >>> if client:
        ...     result = client.table('brands').select('*').execute()
    """
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase client unavailable - package not installed")
        return None
    
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning(
            "Supabase not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY environment variables."
        )
        return None
    
    try:
        client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info(f"Supabase client initialized: {settings.supabase_url}")
        return client
    except Exception as exc:
        logger.error(f"Failed to create Supabase client: {exc}")
        return None


def require_supabase() -> Client:  # type: ignore[valid-type]
    """Return Supabase client or raise if not configured.
    
    Use this when Supabase is absolutely required for the operation.
    
    Returns:
        Configured Supabase client.
    
    Raises:
        SupabaseNotConfigured: If Supabase is not properly configured.
    
    Example:
        >>> client = require_supabase()
        >>> result = client.table('orders').select('*').execute()
    """
    client = get_supabase_client()
    
    if client is None:
        if not SUPABASE_AVAILABLE:
            raise SupabaseNotConfigured(
                "Supabase package is not installed. "
                "Install with: pip install supabase"
            )
        
        raise SupabaseNotConfigured(
            "Supabase is not configured. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY environment variables."
        )
    
    return client


def check_supabase_connection() -> bool:
    """Check if Supabase connection is working.
    
    This is useful for health checks and startup validation.
    
    Returns:
        True if connection is working, False otherwise.
    
    Example:
        >>> if check_supabase_connection():
        ...     print("Supabase is ready")
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Try a simple query to test connection
        result = client.table('product_categories').select('count').limit(1).execute()
        return result is not None
    except Exception as exc:
        logger.error(f"Supabase connection check failed: {exc}")
        return False
