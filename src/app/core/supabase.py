"""Supabase client initialization and utilities."""

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Optional[Client]:
    """Return a cached Supabase client instance.
    
    Returns None if Supabase credentials are not configured.
    This allows the application to run with mock services during testing.
    """
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_supabase_admin_client() -> Optional[Client]:
    """Return a cached Supabase client with service role privileges.
    
    This client bypasses Row Level Security (RLS) and should only be used
    for administrative operations and backend services.
    
    Returns None if Supabase credentials are not configured.
    """
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_database_url() -> Optional[str]:
    """Return the PostgreSQL connection URL for direct database access.
    
    This is useful for running migrations or using SQL directly.
    """
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    
    # Extract project ref from Supabase URL
    # Format: https://PROJECT_REF.supabase.co
    project_ref = settings.supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    return f"postgresql://postgres:{settings.supabase_service_role_key}@db.{project_ref}.supabase.co:5432/postgres"
