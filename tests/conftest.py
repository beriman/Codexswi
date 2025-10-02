from __future__ import annotations

from typing import List

import pytest

from app.services.profile import InMemoryProfileGateway


class FakeSupabaseProfileGateway(InMemoryProfileGateway):
    """Test double exposing follow write operations for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.follow_writes: List[tuple[str, str]] = []
        self.unfollow_writes: List[tuple[str, str]] = []

    async def create_follow(self, *, follower_id: str, following_id: str) -> None:  # type: ignore[override]
        await super().create_follow(follower_id=follower_id, following_id=following_id)
        self.follow_writes.append((follower_id, following_id))

    async def delete_follow(self, *, follower_id: str, following_id: str) -> None:  # type: ignore[override]
        await super().delete_follow(follower_id=follower_id, following_id=following_id)
        self.unfollow_writes.append((follower_id, following_id))

    async def reset_relationships(self) -> None:  # type: ignore[override]
        await super().reset_relationships()
        self.follow_writes.clear()
        self.unfollow_writes.clear()


@pytest.fixture
def fake_profile_gateway() -> FakeSupabaseProfileGateway:
    return FakeSupabaseProfileGateway()
