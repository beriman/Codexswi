"""FastAPI dependency injection utilities.

This module provides reusable dependencies for FastAPI routes, including
database connections, service instances, and session management.

Usage in routes:
    from fastapi import Depends
    from app.core.dependencies import get_db, get_current_user
    
    @router.get("/products")
    async def list_products(db = Depends(get_db)):
        result = db.table('products').select('*').execute()
        return result.data
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status

if TYPE_CHECKING:
    from supabase import Client

from app.core.supabase import get_supabase_client, SupabaseNotConfigured

logger = logging.getLogger(__name__)


async def get_db(request: Request) -> "Client":
    """Provide Supabase client to route handlers via dependency injection.
    
    This dependency will attempt to use the client from app.state first,
    falling back to creating a new client if needed.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Configured Supabase client
    
    Raises:
        HTTPException: If Supabase is not available (503 Service Unavailable)
    
    Example:
        @router.get("/brands")
        async def list_brands(db = Depends(get_db)):
            result = db.table('brands').select('*').execute()
            return result.data
    """
    # Try to get client from app state (preferred)
    if hasattr(request.app.state, 'supabase') and request.app.state.supabase:
        return request.app.state.supabase
    
    # Fallback: create new client
    try:
        client = get_supabase_client()
        if not client:
            raise SupabaseNotConfigured("Supabase client not initialized")
        return client
    except SupabaseNotConfigured as exc:
        logger.error(f"Supabase dependency failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable. Please try again later."
        ) from exc


async def get_current_user(request: Request) -> Optional[dict]:
    """Get currently authenticated user from session.
    
    This dependency extracts user information from the session cookie.
    Returns None if no user is logged in.
    
    Args:
        request: FastAPI request object
    
    Returns:
        User data dict if authenticated, None otherwise
    
    Example:
        @router.get("/profile")
        async def get_profile(user = Depends(get_current_user)):
            if not user:
                raise HTTPException(401, "Not authenticated")
            return {"user": user}
    """
    return request.session.get('user')


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Require authentication for a route.
    
    This dependency ensures a user is logged in, raising 401 if not.
    
    Args:
        user: User from get_current_user dependency
    
    Returns:
        User data dict
    
    Raises:
        HTTPException: 401 if user is not authenticated
    
    Example:
        @router.post("/orders")
        async def create_order(
            user = Depends(require_auth),
            db = Depends(get_db)
        ):
            # User is guaranteed to be authenticated here
            order = db.table('orders').insert({
                'customer_id': user['id'],
                ...
            }).execute()
            return order.data
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role for a route.
    
    This dependency ensures user is authenticated AND has admin role.
    
    Args:
        user: User from require_auth dependency
    
    Returns:
        User data dict
    
    Raises:
        HTTPException: 403 if user is not admin
    
    Example:
        @router.post("/brands/{brand_id}/verify")
        async def verify_brand(
            brand_id: str,
            admin = Depends(require_admin),
            db = Depends(get_db)
        ):
            # Only admins can verify brands
            ...
    """
    role = user.get('role', 'user')
    if role not in ['admin', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def get_optional_db() -> Optional["Client"]:
    """Get Supabase client without raising error if unavailable.
    
    Use this when Supabase is optional and you have fallback logic.
    
    Returns:
        Supabase client if available, None otherwise
    
    Example:
        @router.get("/products")
        async def list_products(db = Depends(get_optional_db)):
            if db:
                # Use Supabase
                result = db.table('products').select('*').execute()
                return result.data
            else:
                # Use fallback (in-memory, cache, etc)
                return get_cached_products()
    """
    return get_supabase_client()
