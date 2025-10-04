"""Routes for the brand storefront experience."""

from __future__ import annotations

import secrets
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import get_settings
from app.services.brands import (
    Brand,
    BrandAlreadyExists,
    BrandError,
    BrandNotFound,
    brand_service,
)
from app.services.profile import ProfileError, ProfileService, profile_service


router = APIRouter()


def get_profile_service() -> ProfileService:
    return profile_service


def _render_brand_form(
    request: Request,
    *,
    title: str,
    form_action: str,
    form_state: Dict[str, Any],
    errors: Dict[str, List[str]] | None = None,
    brand: Brand | None = None,
    status_code: int = status.HTTP_200_OK,
    is_edit: bool = False,
) -> HTMLResponse:
    templates = request.app.state.templates
    settings = get_settings()
    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": title,
        "form_action": form_action,
        "form_state": form_state,
        "errors": errors or {},
        "brand": brand,
        "is_edit": is_edit,
    }
    return templates.TemplateResponse(
        request,
        "pages/brand/form.html",
        context,
        status_code=status_code,
    )


def _render_pending_team_column(
    request: Request,
    brand_slug: str,
    *,
    feedback_message: str | None = None,
    feedback_type: str = "info",
    form_state: Dict[str, str] | None = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    templates = request.app.state.templates
    context = brand_service.get_team_partial_context(brand_slug)
    context.update(
        {
            "request": request,
            "feedback_message": feedback_message,
            "feedback_type": feedback_type,
            "form_state": form_state or {"username": "", "note": ""},
        }
    )
    return templates.TemplateResponse(
        request,
        "components/brand/team_pending_column.html",
        context,
        status_code=status_code,
    )


def _empty_member() -> Dict[str, str]:
    return {
        "profile_id": "",
        "full_name": "",
        "username": "",
        "role": "co-owner",
        "status": "pending",
        "avatar_url": "",
        "expertise": "",
        "invited_by": "",
    }


def _default_form_state() -> Dict[str, Any]:
    member = _empty_member()
    member.update({"role": "owner", "status": "active"})
    return {
        "name": "",
        "slug": "",
        "tagline": "",
        "summary": "",
        "origin_city": "",
        "established_year": "",
        "hero_image_url": "",
        "logo_url": "",
        "aroma_focus": "",
        "story_points": "",
        "is_verified": False,
        "members": [member],
    }


def _form_state_from_brand(brand: Brand) -> Dict[str, Any]:
    return {
        "name": brand.name,
        "slug": brand.slug,
        "tagline": brand.tagline,
        "summary": brand.summary,
        "origin_city": brand.origin_city,
        "established_year": str(brand.established_year),
        "hero_image_url": brand.hero_image_url,
        "logo_url": brand.logo_url or "",
        "aroma_focus": "\n".join(brand.aroma_focus),
        "story_points": "\n".join(brand.story_points),
        "is_verified": brand.is_verified,
        "members": [
            {
                "profile_id": member.profile_id,
                "full_name": member.full_name,
                "username": member.username,
                "role": member.role,
                "status": member.status,
                "avatar_url": member.avatar_url or "",
                "expertise": member.expertise or "",
                "invited_by": member.invited_by or "",
            }
            for member in brand.members
        ],
    }


def _extract_member_indexes(form: Mapping[str, Any]) -> List[str]:
    indexes: set[str] = set()
    for key in form.keys():
        if not key.startswith("members-"):
            continue
        parts = key.split("-")
        if len(parts) >= 3:
            indexes.add(parts[1])
    return sorted(indexes, key=lambda value: int(value) if value.isdigit() else value)


def _parse_members(
    form: Mapping[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, str]], List[str]]:
    payloads: List[Dict[str, Any]] = []
    raw_members: List[Dict[str, str]] = []
    errors: List[str] = []
    indexes = _extract_member_indexes(form)

    for index in indexes:
        prefix = f"members-{index}-"
        raw_member: Dict[str, str] = {
            "profile_id": (form.get(prefix + "profile_id", "") or "").strip(),
            "full_name": (form.get(prefix + "full_name", "") or ""),
            "username": (form.get(prefix + "username", "") or ""),
            "role": (form.get(prefix + "role", "") or ""),
            "status": (form.get(prefix + "status", "") or ""),
            "avatar_url": (form.get(prefix + "avatar_url", "") or ""),
            "expertise": (form.get(prefix + "expertise", "") or ""),
            "invited_by": (form.get(prefix + "invited_by", "") or ""),
        }
        raw_members.append(raw_member)

        meaningful = any((raw_member[key] or "").strip() for key in ("profile_id", "full_name", "username"))
        if not meaningful:
            continue

        full_name = raw_member["full_name"].strip()
        username = raw_member["username"].strip()
        if not full_name or not username:
            errors.append(f"Data member #{int(index) + 1 if index.isdigit() else index} belum lengkap.")
            continue

        payloads.append(
            {
                "profile_id": raw_member["profile_id"],
                "full_name": full_name,
                "username": username,
                "role": raw_member["role"].strip() or ("owner" if not payloads else "co-owner"),
                "status": raw_member["status"].strip() or ("active" if not payloads else "pending"),
                "avatar_url": raw_member["avatar_url"],
                "expertise": raw_member["expertise"],
                "invited_by": raw_member["invited_by"],
            }
        )

    return payloads, raw_members, errors


def _form_state_from_submission(
    form: Mapping[str, Any],
    *,
    fallback_slug: str | None = None,
    default_members: Iterable[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    members = list(default_members or [])
    _, raw_members, _ = _parse_members(form)
    if raw_members:
        members = raw_members

    def _get(key: str, default: str = "") -> str:
        value = form.get(key)
        if value is None:
            return default
        return str(value)

    return {
        "name": _get("name"),
        "slug": _get("slug", fallback_slug or "") or (fallback_slug or ""),
        "tagline": _get("tagline"),
        "summary": _get("summary"),
        "origin_city": _get("origin_city"),
        "established_year": _get("established_year"),
        "hero_image_url": _get("hero_image_url"),
        "logo_url": _get("logo_url"),
        "aroma_focus": _get("aroma_focus"),
        "story_points": _get("story_points"),
        "is_verified": bool(form.get("is_verified")),
        "members": members if members else list(default_members or []),
    }


def _split_to_list(value: str) -> List[str]:
    pieces: List[str] = []
    for line in value.splitlines():
        for part in line.split(","):
            cleaned = part.strip()
            if cleaned:
                pieces.append(cleaned)
    return pieces


def _normalise_errors(raw_errors: Mapping[str, Iterable[str]]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for field, messages in raw_errors.items():
        result[field] = list(messages)
    return result


@router.get("/brands/new", response_class=HTMLResponse, name="new_brand")
async def new_brand(request: Request) -> HTMLResponse:
    form_state = _default_form_state()
    return _render_brand_form(
        request,
        title="Buat Brand Baru",
        form_action="/brands",
        form_state=form_state,
    )


@router.get("/brands/{slug}/edit", response_class=HTMLResponse, name="edit_brand")
async def edit_brand(request: Request, slug: str) -> HTMLResponse:
    try:
        brand = brand_service.get_brand(slug)
    except BrandNotFound as exc:  # pragma: no cover - handled by exception mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    form_state = _form_state_from_brand(brand)
    return _render_brand_form(
        request,
        title=f"Edit Brand {brand.name}",
        form_action=f"/brands/{brand.slug}",
        form_state=form_state,
        brand=brand,
        is_edit=True,
    )


def _handle_members_update(
    *,
    brand_slug: str,
    member_payloads: List[Dict[str, Any]],
) -> None:
    if not member_payloads:
        raise BrandError("Minimal satu member brand wajib tersedia.")
    brand_service.update_members(brand_slug, members=member_payloads)


def _create_brand_from_form(form: Mapping[str, Any]) -> Brand:
    member_payloads, _, member_errors = _parse_members(form)
    if member_errors:
        raise BrandError("; ".join(member_errors))
    owner = next((member for member in member_payloads if member.get("role") == "owner"), None)
    if not owner:
        raise BrandError("Minimal satu owner brand aktif wajib diisi.")

    brand = brand_service.create_brand(
        owner_profile_id=owner.get("profile_id") or secrets.token_urlsafe(6),
        owner_name=owner["full_name"],
        owner_username=owner["username"],
        owner_avatar=owner.get("avatar_url") or None,
        name=str(form.get("name", "")),
        slug=str(form.get("slug") or ""),
        tagline=str(form.get("tagline", "")),
        summary=str(form.get("summary", "")),
        origin_city=str(form.get("origin_city", "")),
        established_year=str(form.get("established_year", "")),
        hero_image_url=str(form.get("hero_image_url", "")),
        logo_url=str(form.get("logo_url") or "") or None,
        aroma_focus=_split_to_list(str(form.get("aroma_focus", ""))),
        story_points=_split_to_list(str(form.get("story_points", ""))),
        is_verified=bool(form.get("is_verified")),
    )

    _handle_members_update(brand_slug=brand.slug, member_payloads=member_payloads)
    return brand


def _update_brand_from_form(form: Mapping[str, Any], *, slug: str) -> Brand:
    member_payloads, _, member_errors = _parse_members(form)
    if member_errors:
        raise BrandError("; ".join(member_errors))

    brand = brand_service.update_brand(
        slug,
        name=str(form.get("name", "")),
        slug=str(form.get("slug") or ""),
        tagline=str(form.get("tagline", "")),
        summary=str(form.get("summary", "")),
        origin_city=str(form.get("origin_city", "")),
        established_year=str(form.get("established_year", "")),
        hero_image_url=str(form.get("hero_image_url", "")),
        logo_url=str(form.get("logo_url") or "") or None,
        aroma_focus=_split_to_list(str(form.get("aroma_focus", ""))),
        story_points=_split_to_list(str(form.get("story_points", ""))),
        is_verified=bool(form.get("is_verified")),
    )

    _handle_members_update(brand_slug=brand.slug, member_payloads=member_payloads)
    return brand


@router.post("/brands", response_class=HTMLResponse, name="create_brand")
async def create_brand(request: Request) -> HTMLResponse:
    form = await request.form()
    errors: MutableMapping[str, List[str]] = {}
    form_state = _form_state_from_submission(form, default_members=_default_form_state()["members"])

    try:
        brand = _create_brand_from_form(form)
    except BrandAlreadyExists as exc:
        errors.setdefault("slug", []).append(str(exc))
    except BrandError as exc:
        errors.setdefault("__all__", []).append(str(exc))
    else:
        location = f"/brands/{brand.slug}"
        return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)

    return _render_brand_form(
        request,
        title="Buat Brand Baru",
        form_action="/brands",
        form_state=form_state,
        errors=_normalise_errors(errors),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.api_route(
    "/brands/{slug}",
    methods=["POST", "PATCH"],
    response_class=HTMLResponse,
    name="update_brand",
)
async def update_brand(request: Request, slug: str) -> HTMLResponse:
    form = await request.form()
    errors: MutableMapping[str, List[str]] = {}

    try:
        existing_brand = brand_service.get_brand(slug)
    except BrandNotFound as exc:  # pragma: no cover - handled upstream
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    fallback_members = [
        {
            "profile_id": member.profile_id,
            "full_name": member.full_name,
            "username": member.username,
            "role": member.role,
            "status": member.status,
            "avatar_url": member.avatar_url or "",
            "expertise": member.expertise or "",
            "invited_by": member.invited_by or "",
        }
        for member in existing_brand.members
    ]

    form_state = _form_state_from_submission(
        form,
        fallback_slug=existing_brand.slug,
        default_members=fallback_members,
    )

    try:
        brand = _update_brand_from_form(form, slug=slug)
    except BrandAlreadyExists as exc:
        errors.setdefault("slug", []).append(str(exc))
    except BrandError as exc:
        errors.setdefault("__all__", []).append(str(exc))
    else:
        location = f"/brands/{brand.slug}?updated=1"
        return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)

    return _render_brand_form(
        request,
        title=f"Edit Brand {existing_brand.name}",
        form_action=f"/brands/{existing_brand.slug}",
        form_state=form_state,
        errors=_normalise_errors(errors),
        brand=existing_brand,
        is_edit=True,
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.get("/brands/{slug}", response_class=HTMLResponse)
async def read_brand(request: Request, slug: str) -> HTMLResponse:
    """Render the public brand page with collaboration summary."""

    templates = request.app.state.templates
    settings = get_settings()

    try:
        brand = brand_service.get_brand(slug)
    except BrandNotFound as exc:  # pragma: no cover - handled via exception mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": brand.name,
        "brand": brand,
    }
    return templates.TemplateResponse(request, "pages/brand/detail.html", context)


@router.get("/brands", response_class=HTMLResponse)
async def list_brands(request: Request) -> HTMLResponse:
    """Simple directory view to help merchant explore brand pages."""

    templates = request.app.state.templates
    settings = get_settings()
    brands = list(brand_service.list_brands())

    context = {
        "request": request,
        "app_name": settings.app_name,
        "environment": settings.environment,
        "title": "Brand Partner",
        "brands": brands,
    }
    return templates.TemplateResponse(request, "pages/brand/index.html", context)


@router.post(
    "/brands/{slug}/co-owners",
    response_class=HTMLResponse,
    name="invite_brand_co_owner",
)
async def invite_brand_co_owner(
    request: Request,
    slug: str,
    username: str = Form(...),
    note: str = Form(default=""),
    profile_service: ProfileService = Depends(get_profile_service),
) -> HTMLResponse:
    try:
        profile_view = await profile_service.get_profile(username)
    except ProfileError as exc:
        return _render_pending_team_column(
            request,
            slug,
            feedback_message=exc.message,
            feedback_type="error",
            form_state={"username": username, "note": note},
        )

    try:
        brand = brand_service.get_brand(slug)
        invited_by = brand.list_owners()[0].full_name if brand.list_owners() else None
        brand_service.invite_co_owner(
            slug,
            profile_id=profile_view.profile.id,
            full_name=profile_view.profile.full_name,
            username=profile_view.profile.username,
            expertise=profile_view.profile.preferred_aroma,
            avatar_url=profile_view.profile.avatar_url,
            invited_by=invited_by,
        )
    except BrandError as exc:
        return _render_pending_team_column(
            request,
            slug,
            feedback_message=exc.message,
            feedback_type="error",
            form_state={"username": username, "note": note},
        )

    feedback = f"Undangan co-owner dikirim ke {profile_view.profile.full_name}."
    if note.strip():
        feedback += " Catatan ikut diteruskan."

    return _render_pending_team_column(
        request,
        slug,
        feedback_message=feedback,
        feedback_type="success",
    )


@router.post(
    "/brands/{slug}/co-owners/{profile_id}/approve",
    response_class=HTMLResponse,
    name="approve_brand_co_owner",
)
async def approve_brand_co_owner(
    request: Request,
    slug: str,
    profile_id: str,
) -> HTMLResponse:
    try:
        member = brand_service.approve_co_owner(slug, profile_id)
    except BrandError as exc:
        return _render_pending_team_column(
            request,
            slug,
            feedback_message=exc.message,
            feedback_type="error",
        )

    feedback = f"{member.full_name} sekarang menjadi co-owner aktif."
    return _render_pending_team_column(
        request,
        slug,
        feedback_message=feedback,
        feedback_type="success",
    )


@router.delete(
    "/brands/{slug}/co-owners/{profile_id}",
    response_class=HTMLResponse,
    name="cancel_brand_co_owner",
)
async def cancel_brand_co_owner(
    request: Request,
    slug: str,
    profile_id: str,
) -> HTMLResponse:
    try:
        member = brand_service.cancel_co_owner_invite(slug, profile_id)
    except BrandError as exc:
        return _render_pending_team_column(
            request,
            slug,
            feedback_message=exc.message,
            feedback_type="error",
        )

    feedback = f"Undangan untuk {member.full_name} dibatalkan."
    return _render_pending_team_column(
        request,
        slug,
        feedback_message=feedback,
        feedback_type="success",
    )

