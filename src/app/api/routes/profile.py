"""Profile detail and follow interaction endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from app.services.profile import (
    ProfileError,
    ProfileService,
    ProfileView,
    profile_service,
)


router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_service() -> ProfileService:
    return profile_service


def _viewer_query_param(viewer_id: str | None) -> str:
    return f"viewer={viewer_id}" if viewer_id else ""


@router.get("/{username}", response_class=HTMLResponse, name="profile_detail")
async def profile_detail(
    username: str,
    request: Request,
    viewer: str | None = Query(default=None),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    profile_view = await service.get_profile(username, viewer_id=viewer)
    templates = request.app.state.templates
    context = {
        "request": request,
        "profile_view": profile_view,
        "profile": profile_view.profile,
        "stats": profile_view.stats,
        "viewer_query": _viewer_query_param(profile_view.viewer.id),
    }
    return templates.TemplateResponse(request, "pages/profile/detail.html", context)


def _render_follow_button(
    request: Request,
    profile_view: ProfileView,
) -> HTMLResponse:
    templates = request.app.state.templates
    context = {
        "request": request,
        "profile_view": profile_view,
        "profile": profile_view.profile,
        "stats": profile_view.stats,
        "viewer_query": _viewer_query_param(profile_view.viewer.id),
    }
    return templates.TemplateResponse(request, "components/profile/follow_button.html", context)


@router.post("/{username}/follow", response_class=HTMLResponse, name="profile_follow")
async def follow_profile(
    username: str,
    request: Request,
    viewer: str | None = Query(default=None),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    if not viewer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Viewer wajib diisi")

    try:
        profile_view = await service.follow_profile(username, follower_id=viewer)
    except ProfileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _render_follow_button(request, profile_view)


@router.delete("/{username}/follow", response_class=HTMLResponse, name="profile_unfollow")
async def unfollow_profile(
    username: str,
    request: Request,
    viewer: str | None = Query(default=None),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    if not viewer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Viewer wajib diisi")

    try:
        profile_view = await service.unfollow_profile(username, follower_id=viewer)
    except ProfileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _render_follow_button(request, profile_view)


@router.get("/{username}/followers", response_class=HTMLResponse, name="profile_followers")
async def followers_modal(
    username: str,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    followers = await service.list_followers(username)
    profile_view = await service.get_profile(username)
    templates = request.app.state.templates
    context = {
        "title": "Pengikut",
        "profiles": followers,
        "profile": profile_view.profile,
        "request": request,
    }
    return templates.TemplateResponse(request, "components/profile/user_list.html", context)


@router.get("/{username}/following", response_class=HTMLResponse, name="profile_following")
async def following_modal(
    username: str,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    following = await service.list_following(username)
    profile_view = await service.get_profile(username)
    templates = request.app.state.templates
    context = {
        "title": "Mengikuti",
        "profiles": following,
        "profile": profile_view.profile,
        "request": request,
    }
    return templates.TemplateResponse(request, "components/profile/user_list.html", context)


TAB_TEMPLATES: Dict[str, str] = {
    "aktivitas": "components/profile/tab_activity.html",
    "favorit": "components/profile/tab_favorites.html",
    "sambatan": "components/profile/tab_sambatan.html",
    "karya": "components/profile/perfumer_products.html",
    "brand": "components/profile/brand_cards.html",
}


@router.get("/{username}/tab/{tab}", response_class=HTMLResponse, name="profile_tab")
async def profile_tab(
    username: str,
    tab: str,
    request: Request,
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    tab = tab.lower()
    if tab not in TAB_TEMPLATES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tab tidak ditemukan")

    profile_view = await service.get_profile(username)
    templates = request.app.state.templates

    context = {
        "profile_view": profile_view,
        "profile": profile_view.profile,
        "request": request,
    }

    if tab == "karya":
        context["products"] = await service.list_perfumer_products(username)
    elif tab == "brand":
        context["brands"] = await service.list_owned_brands(username)

    template_name = TAB_TEMPLATES[tab]
    return templates.TemplateResponse(request, template_name, context)
