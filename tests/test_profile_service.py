import asyncio

import pytest

from app.services.profile import ProfileError, ProfileService
from tests.conftest import FakeSupabaseProfileGateway


@pytest.fixture
def profile_service(fake_profile_gateway: FakeSupabaseProfileGateway) -> ProfileService:
    service = ProfileService(gateway=fake_profile_gateway)
    asyncio.run(service.reset_relationships())
    return service


def test_get_profile_returns_badges_and_stats(
    profile_service: ProfileService,
) -> None:
    view = asyncio.run(profile_service.get_profile("amelia-damayanti"))

    assert view.profile.full_name == "Amelia Damayanti"
    assert view.stats.follower_count == 2
    badge_slugs = {badge.slug for badge in view.badges}
    assert "perfumer" in badge_slugs
    assert "brand-owner" in badge_slugs


def test_follow_profile_updates_relationship(
    profile_service: ProfileService, fake_profile_gateway: FakeSupabaseProfileGateway
) -> None:
    view = asyncio.run(
        profile_service.follow_profile("chandra-pratama", follower_id="user_bintang")
    )

    assert view.stats.follower_count >= 1
    assert ("user_bintang", "user_chandra") in fake_profile_gateway.follow_writes
    viewer_state = asyncio.run(
        profile_service.get_profile("chandra-pratama", viewer_id="user_bintang")
    )
    assert viewer_state.viewer.is_following is True


def test_unfollow_profile_resets_relationship(
    profile_service: ProfileService, fake_profile_gateway: FakeSupabaseProfileGateway
) -> None:
    asyncio.run(profile_service.follow_profile("chandra-pratama", follower_id="user_bintang"))
    view = asyncio.run(
        profile_service.unfollow_profile("chandra-pratama", follower_id="user_bintang")
    )

    assert view.stats.follower_count >= 0
    assert ("user_bintang", "user_chandra") in fake_profile_gateway.unfollow_writes
    viewer_state = asyncio.run(
        profile_service.get_profile("chandra-pratama", viewer_id="user_bintang")
    )
    assert viewer_state.viewer.is_following is False


def test_cannot_follow_self(profile_service: ProfileService) -> None:
    with pytest.raises(ProfileError):
        asyncio.run(
            profile_service.follow_profile("user_bintang", follower_id="user_bintang")
        )
