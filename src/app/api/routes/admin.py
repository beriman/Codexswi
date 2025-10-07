"""Admin API routes for platform management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

from app.core.dependencies import get_db
from app.services.settings import SettingsService

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin_user(request: Request) -> dict:
    """Require admin user from session with fail-closed security.
    
    SECURITY: Fails closed - denies access if admin configuration is missing.
    
    Admin access control via environment variables:
    - ADMIN_USER_IDS: Comma-separated list of allowed user IDs
    - ADMIN_EMAILS: Comma-separated list of allowed admin emails
    
    At least ONE of these must be configured or all requests will be denied (403).
    
    Example:
        ADMIN_USER_IDS=abc-123-def,xyz-789-uvw
        ADMIN_EMAILS=admin@sensasiwangi.id,manager@sensasiwangi.id
    """
    import os
    
    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get admin configuration from environment
    admin_user_ids = os.getenv('ADMIN_USER_IDS', '').split(',')
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    
    # Clean whitespace
    admin_user_ids = [uid.strip() for uid in admin_user_ids if uid.strip()]
    admin_emails = [email.strip().lower() for email in admin_emails if email.strip()]
    
    # FAIL CLOSED: If no admin config, deny all access
    if not admin_user_ids and not admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Admin access denied: No admin users configured. "
                "Set ADMIN_USER_IDS or ADMIN_EMAILS environment variable."
            )
        )
    
    # Check if user is admin
    user_id = user.get('user_id')
    user_email = user.get('email', '').lower()
    
    is_admin = False
    
    if admin_user_ids and user_id in admin_user_ids:
        is_admin = True
    elif admin_emails and user_email in admin_emails:
        is_admin = True
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Your account is not authorized for admin functions."
        )
    
    return user


class PlatformSettingsResponse(BaseModel):
    """Platform settings response."""
    bank_account_number: str
    bank_account_name: str
    bank_name: str
    platform_fee_rate: Decimal
    updated_at: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class UpdatePlatformSettingsRequest(BaseModel):
    """Request to update platform settings."""
    bank_account_number: Optional[str] = Field(None, min_length=5, max_length=50)
    bank_account_name: Optional[str] = Field(None, min_length=3, max_length=255)
    bank_name: Optional[str] = Field(None, min_length=2, max_length=100)
    platform_fee_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    
    @validator('platform_fee_rate')
    def validate_fee_rate(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Platform fee rate must be between 0 and 100')
        return v


@router.get("/settings", response_model=PlatformSettingsResponse)
async def get_platform_settings(
    request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(require_admin_user)
):
    """Get current platform settings.
    
    Requires admin authentication. Settings include bank account and fee configuration.
    """
    try:
        settings_service = SettingsService(db)
        settings = await settings_service.get_settings()
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve platform settings: {str(e)}"
        )


@router.put("/settings", response_model=PlatformSettingsResponse)
async def update_platform_settings(
    settings_request: UpdatePlatformSettingsRequest,
    http_request: Request,
    db=Depends(get_db),
    current_user: dict = Depends(require_admin_user)
):
    """Update platform settings.
    
    Admin only endpoint to update bank account and fee configuration.
    At least one field must be provided.
    """
    # Check if at least one field is provided
    if all(v is None for v in settings_request.dict().values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    try:
        settings_service = SettingsService(db)
        updated_settings = await settings_service.update_settings(
            bank_account_number=settings_request.bank_account_number,
            bank_account_name=settings_request.bank_account_name,
            bank_name=settings_request.bank_name,
            platform_fee_rate=settings_request.platform_fee_rate,
            updated_by=current_user.get('user_id')
        )
        return updated_settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update platform settings: {str(e)}"
        )
