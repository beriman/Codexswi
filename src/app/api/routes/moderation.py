"""
Moderation API routes for brand verification and content curation.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.services.brands import BrandService, BrandNotFound, BrandError

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


def get_brand_service() -> BrandService:
    """Dependency to get brand service instance."""
    from app.services.brands import brand_service
    return brand_service


class BrandModerationRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|request_revision)$")
    notes: Optional[str] = Field(None, max_length=500)


class BrandModerationResponse(BaseModel):
    success: bool
    message: str
    brand_slug: str
    is_verified: bool


@router.post("/brands/{slug}", response_model=BrandModerationResponse)
def moderate_brand(
    slug: str,
    payload: BrandModerationRequest,
    service: BrandService = Depends(get_brand_service),
) -> BrandModerationResponse:
    """
    Moderate brand verification status.
    
    Actions:
    - approve: Set is_verified=True
    - reject: Set is_verified=False
    - request_revision: Set is_verified=False with notes
    """
    try:
        brand = service.get_brand(slug)
    except BrandNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    
    action = payload.action
    is_verified = False
    message = ""
    
    if action == "approve":
        is_verified = True
        message = f"Brand '{brand.name}' berhasil disetujui dan diverifikasi"
        # Update brand verification status
        service.update_brand(
            slug,
            name=brand.name,
            slug=brand.slug,
            tagline=brand.tagline,
            summary=brand.summary,
            origin_city=brand.origin_city,
            established_year=brand.established_year,
            hero_image_url=brand.hero_image_url,
            logo_url=brand.logo_url,
            aroma_focus=brand.aroma_focus,
            story_points=brand.story_points,
            is_verified=True,
        )
        
    elif action == "reject":
        message = f"Brand '{brand.name}' ditolak"
        if payload.notes:
            message += f" - Catatan: {payload.notes}"
        # Update brand verification status
        service.update_brand(
            slug,
            name=brand.name,
            slug=brand.slug,
            tagline=brand.tagline,
            summary=brand.summary,
            origin_city=brand.origin_city,
            established_year=brand.established_year,
            hero_image_url=brand.hero_image_url,
            logo_url=brand.logo_url,
            aroma_focus=brand.aroma_focus,
            story_points=brand.story_points,
            is_verified=False,
        )
        
    elif action == "request_revision":
        message = f"Permintaan revisi dikirim untuk brand '{brand.name}'"
        if payload.notes:
            message += f" - Catatan: {payload.notes}"
        # Keep is_verified=False for revision requests
        service.update_brand(
            slug,
            name=brand.name,
            slug=brand.slug,
            tagline=brand.tagline,
            summary=brand.summary,
            origin_city=brand.origin_city,
            established_year=brand.established_year,
            hero_image_url=brand.hero_image_url,
            logo_url=brand.logo_url,
            aroma_focus=brand.aroma_focus,
            story_points=brand.story_points,
            is_verified=False,
        )
    
    return BrandModerationResponse(
        success=True,
        message=message,
        brand_slug=slug,
        is_verified=is_verified,
    )
