"""Profile detail and follow interaction endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.profile import (
    ProfileError,
    ProfileService,
    ProfileUpdate,
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


def _ensure_viewer(viewer: str | None) -> str:
    if not viewer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Viewer wajib diisi")
    return viewer


def _build_profile_update(
    *,
    full_name: str,
    bio: str,
    preferred_aroma: str,
    avatar_url: str,
    location: str,
) -> ProfileUpdate:
    name = full_name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nama wajib diisi")

    def _optional(value: str) -> str | None:
        trimmed = value.strip()
        return trimmed or None

    return ProfileUpdate(
        full_name=name,
        bio=_optional(bio),
        preferred_aroma=_optional(preferred_aroma),
        avatar_url=_optional(avatar_url),
        location=_optional(location),
    )


@router.get("/{username}/edit", response_class=HTMLResponse, name="profile_edit")
async def edit_profile(
    username: str,
    request: Request,
    viewer: str | None = Query(default=None),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    viewer_id = _ensure_viewer(viewer)
    profile_view = await service.get_profile(username, viewer_id=viewer_id)
    if not profile_view.viewer.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya pemilik profil yang dapat melakukan perubahan.",
        )

    templates = request.app.state.templates
    context = {
        "request": request,
        "profile_view": profile_view,
        "profile": profile_view.profile,
        "viewer_query": _viewer_query_param(profile_view.viewer.id),
        "feedback": None,
    }
    return templates.TemplateResponse(request, "pages/profile/edit.html", context)


@router.api_route("/{username}", methods=["POST", "PATCH"], response_class=HTMLResponse, name="profile_update")
async def update_profile(
    username: str,
    request: Request,
    viewer: str | None = Query(default=None),
    full_name: str = Form(...),
    bio: str = Form(""),
    location: str = Form(""),
    preferred_aroma: str = Form(""),
    avatar_url: str = Form(""),
    service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    viewer_id = _ensure_viewer(viewer)
    payload = _build_profile_update(
        full_name=full_name,
        bio=bio,
        preferred_aroma=preferred_aroma,
        avatar_url=avatar_url,
        location=location,
    )

    try:
        profile_view, changes_applied = await service.update_profile(
            username, viewer_id=viewer_id, payload=payload
        )
    except ProfileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if request.headers.get("hx-request"):
        templates = request.app.state.templates
        context = {
            "request": request,
            "profile_view": profile_view,
            "profile": profile_view.profile,
            "viewer_query": _viewer_query_param(profile_view.viewer.id),
            "feedback": {
                "status": "success" if changes_applied else "info",
                "message": (
                    "Profil berhasil diperbarui."
                    if changes_applied
                    else "Tidak ada perubahan yang disimpan."
                ),
            },
        }
        return templates.TemplateResponse(
            request,
            "components/profile/edit_form.html",
            context,
        )

    redirect_url = request.url_for("profile_detail", username=profile_view.profile.username)
    if profile_view.viewer.id:
        redirect_url = f"{redirect_url}?{_viewer_query_param(profile_view.viewer.id)}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
