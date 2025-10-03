"""Integration tests for the moderation dashboard route."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.application import create_app
from app.services.moderation_repository import ModerationDashboardRepository


def test_moderation_dashboard_renders_snapshot_artifacts() -> None:
    """The moderation dashboard should render data returned by the service."""

    repository = ModerationDashboardRepository()
    snapshot = repository.fetch_dashboard_snapshot()
    snapshot["persona"]["name"] = "Repository Persona"

    fake_service = MagicMock()
    fake_service.get_snapshot.return_value = snapshot

    app = create_app()
    app.state.moderation_dashboard_service = fake_service

    with TestClient(app) as client:
        response = client.get("/dashboard/moderation")

    assert response.status_code == 200
    body = response.text
    assert "Repository Persona" in body
    fake_service.get_snapshot.assert_called_once_with()
