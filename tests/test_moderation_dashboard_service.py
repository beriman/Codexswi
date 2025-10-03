"""Unit tests for the moderation dashboard service."""

from unittest.mock import MagicMock

from app.services.moderation_dashboard import ModerationDashboardService


def test_service_uses_repository_snapshot() -> None:
    """The service should delegate snapshot generation to the repository."""

    repository = MagicMock()
    repository.fetch_dashboard_snapshot.return_value = {"persona": {"name": "Mock"}}

    service = ModerationDashboardService(repository=repository)

    snapshot = service.get_snapshot()

    repository.fetch_dashboard_snapshot.assert_called_once_with()
    assert snapshot["persona"]["name"] == "Mock"
