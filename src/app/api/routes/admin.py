"""Admin API routes for platform management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

from app.core.dependencies import get_db
from app.services.auth import require_authenticated_user
from app.services.settings import SettingsService

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
    current_user: dict = Depends(require_authenticated_user)
):
    """Get current platform settings.
    
    Requires authentication. Settings include bank account and fee configuration.
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
    current_user: dict = Depends(require_authenticated_user)
):
    """Update platform settings.
    
    Admin only endpoint to update bank account and fee configuration.
    At least one field must be provided.
    """
    # TODO: Add admin role check here
    # For now, any authenticated user can update (will be restricted in production)
    
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
