"""
Team management API routes for inviting and managing brand members.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.services.brands import BrandService, BrandNotFound, BrandMemberExists, BrandError

router = APIRouter(prefix="/api/team", tags=["team"])


def get_brand_service() -> BrandService:
    """Dependency to get brand service instance."""
    from app.services.brands import brand_service
    return brand_service


class TeamInviteRequest(BaseModel):
    brand_slug: str = Field(..., min_length=1)
    profile_id: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=3, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    expertise: str | None = Field(None, max_length=200)
    invited_by: str | None = None


class TeamInviteResponse(BaseModel):
    success: bool
    message: str
    member_profile_id: str
    member_name: str
    member_role: str
    member_status: str


@router.post("/invite", response_model=TeamInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_team_member(
    payload: TeamInviteRequest,
    service: BrandService = Depends(get_brand_service),
) -> TeamInviteResponse:
    """Invite a new co-owner to a brand."""
    try:
        member = service.invite_co_owner(
            brand_slug=payload.brand_slug,
            profile_id=payload.profile_id,
            full_name=payload.full_name,
            username=payload.username,
            expertise=payload.expertise,
            avatar_url=None,
            invited_by=payload.invited_by,
        )
        
        return TeamInviteResponse(
            success=True,
            message=f"{payload.full_name} berhasil diundang sebagai co-owner",
            member_profile_id=member.profile_id,
            member_name=member.full_name,
            member_role=member.role,
            member_status=member.status,
        )
        
    except BrandNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BrandMemberExists as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except BrandError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
