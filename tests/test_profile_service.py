import pytest

from app.services.profile import ProfileError, profile_service


@pytest.fixture(autouse=True)
def reset_profile_service() -> None:
    profile_service.reset_relationships()
    yield
    profile_service.reset_relationships()


def test_get_profile_returns_badges_and_stats() -> None:
    view = profile_service.get_profile("amelia-damayanti")

    assert view.profile.full_name == "Amelia Damayanti"
    assert view.stats.follower_count == 2
    badge_slugs = {badge.slug for badge in view.badges}
    assert "perfumer" in badge_slugs
    assert "brand-owner" in badge_slugs


def test_follow_profile_updates_relationship() -> None:
    view = profile_service.follow_profile("chandra-pratama", follower_id="user_bintang")

    assert view.stats.follower_count >= 1
    viewer_state = profile_service.get_profile("chandra-pratama", viewer_id="user_bintang").viewer
    assert viewer_state.is_following is True


def test_unfollow_profile_resets_relationship() -> None:
    profile_service.follow_profile("chandra-pratama", follower_id="user_bintang")
    view = profile_service.unfollow_profile("chandra-pratama", follower_id="user_bintang")

    assert view.stats.follower_count >= 0
    viewer_state = profile_service.get_profile("chandra-pratama", viewer_id="user_bintang").viewer
    assert viewer_state.is_following is False


def test_cannot_follow_self() -> None:
    with pytest.raises(ProfileError):
        profile_service.follow_profile("user_bintang", follower_id="user_bintang")
