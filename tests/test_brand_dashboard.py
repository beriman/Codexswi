"""Tests for the brand owner dashboard demo snapshot and route."""

from fastapi.testclient import TestClient

from app.core.application import create_app
from app.services.brand_dashboard import BrandOwnerDashboardService


class TestBrandOwnerDashboardService:
    """Unit level assertions for the dashboard snapshot payload."""

    def setup_method(self) -> None:
        self.service = BrandOwnerDashboardService()

    def test_snapshot_contains_expected_sections(self) -> None:
        snapshot = self.service.get_snapshot()

        assert snapshot["brand_profile"]["brand_name"] == "Studio Senja"
        assert len(snapshot["kpis"]) >= 4
        assert len(snapshot["order_statuses"]) >= 4
        assert len(snapshot["products"]) >= 4
        assert len(snapshot["orders"]) >= 4
        assert len(snapshot["promotions"]) >= 3
        assert len(snapshot["verification_steps"]) >= 3
        assert len(snapshot["team_members"]) >= 3
        assert len(snapshot["activity_log"]) >= 3

    def test_analytics_ranges_are_well_formed(self) -> None:
        snapshot = self.service.get_snapshot()
        ranges = snapshot["analytics_ranges"]

        assert ranges, "Expected at least one analytics dataset"

        for dataset in ranges:
            assert {"key", "label", "summary", "points", "x_labels"} <= dataset.keys()
            summary = dataset["summary"]
            assert {"revenue", "orders", "avg_order", "conversion"} <= summary.keys()
            points = dataset["points"]
            labels = dataset["x_labels"]
            assert len(points) == len(labels)
            assert all(isinstance(point, (int, float)) for point in points)


def test_brand_owner_dashboard_route_renders_snapshot_data() -> None:
    """The dashboard page should render key snapshot copy for smoke coverage."""

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/dashboard/brand-owner")

    assert response.status_code == 200
    body = response.text
    assert "Dashboard Brand Owner" in body
    assert "Studio Senja" in body
    assert "Voucher Loyalis Ramadan" in body
