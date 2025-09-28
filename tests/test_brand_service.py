"""Unit tests for the in-memory brand service."""

import pytest

from app.services.brands import (
    BrandAlreadyExists,
    BrandError,
    BrandMemberExists,
    BrandService,
)


def create_service() -> BrandService:
    """Helper to create a fresh service with seeded data for each test."""

    return BrandService()


def test_search_brands_matches_by_tagline() -> None:
    service = create_service()

    results = service.search_brands("nostalgia")

    assert results, "Expected at least one search result"
    assert results[0].slug == "langit-senja"


def test_create_brand_registers_owner_and_unique_slug() -> None:
    service = create_service()

    brand = service.create_brand(
        owner_profile_id="user_diah",
        owner_name="Diah Lestari",
        owner_username="diah-lestari",
        owner_avatar=None,
        name="Aroma Harmoni",
        tagline="Eksplorasi aroma herbal dan teh fermentasi",
        summary="Brand eksperimen aroma yang fokus pada bahan botani hasil fermentasi.",
        origin_city="Semarang, Indonesia",
        established_year=2022,
        hero_image_url="https://example.com/hero.jpg",
        aroma_focus=["Herbal", "Fermentasi"],
        logo_url=None,
    )

    assert brand.slug == "aroma-harmoni"
    assert brand.list_active_members()[0].role == "owner"
    assert brand.list_owners()[0].full_name == "Diah Lestari"
    assert brand.established_year == 2022
    assert not brand.is_verified

    with pytest.raises(BrandAlreadyExists):
        service.create_brand(
            owner_profile_id="user_other",
            owner_name="Orang Lain",
            owner_username="orang-lain",
            owner_avatar=None,
            name="Aroma Harmoni",
            tagline="",
            summary="",
            origin_city="",
            established_year=2022,
            hero_image_url="https://example.com/hero.jpg",
            logo_url=None,
        )


def test_invite_and_approve_co_owner() -> None:
    service = create_service()
    brand = service.get_brand("studio-senja")

    pending_before = len(brand.list_pending_members())

    invitation = service.invite_co_owner(
        brand.slug,
        profile_id="user_farhan",
        full_name="Farhan Nugraha",
        username="farhan-nugraha",
        expertise="Operasional",
    )

    assert invitation.is_pending
    assert len(brand.list_pending_members()) == pending_before + 1

    with pytest.raises(BrandMemberExists):
        service.invite_co_owner(
            brand.slug,
            profile_id="user_farhan",
            full_name="Farhan Nugraha",
            username="farhan-nugraha",
        )

    approved = service.approve_co_owner(brand.slug, "user_farhan")

    assert approved.status == "active"
    assert not approved.is_pending

    with pytest.raises(BrandError):
        service.approve_co_owner(brand.slug, "user_tidak_ada")


def test_update_logo_assigns_and_replaces_brand_logo() -> None:
    service = create_service()
    brand = service.get_brand("langit-senja")

    assert brand.logo_url is not None

    updated = service.update_logo(brand.slug, logo_url="https://example.com/new-logo.png")

    assert updated.logo_url == "https://example.com/new-logo.png"

    cleared = service.update_logo(brand.slug, logo_url=None)

    assert cleared.logo_url is None

