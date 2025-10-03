"""Integration tests for the moderation dashboard route."""

from fastapi.testclient import TestClient

from app.core.application import create_app


def test_moderation_dashboard_renders_snapshot_artifacts() -> None:
    """The moderation dashboard should render the demo snapshot data."""

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/dashboard/moderation")

    assert response.status_code == 200
    body = response.text
    assert "Dashboard Moderasi" in body or "Arif Santoso" in body
