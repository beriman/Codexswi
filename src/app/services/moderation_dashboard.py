"""Demo data provider for the moderation, admin, and curator dashboard."""

from __future__ import annotations

from typing import Optional

from app.services.moderation_models import (
    AuditTrailEntry,
    ContactPoint,
    CurationSubmission,
    HeatmapSlot,
    HelpResource,
    InsightTrend,
    ModerationAlert,
    ModerationKPI,
    PendingInvitation,
    PolicyUpdate,
    ReportTicket,
    TeamMemberSummary,
)
from app.services.moderation_repository import ModerationDashboardRepository


class ModerationDashboardService:
    """Encapsulates moderation dashboard orchestration."""

    def __init__(self, repository: Optional[ModerationDashboardRepository] = None) -> None:
        self._repository = repository or ModerationDashboardRepository()

    def get_snapshot(self) -> dict:
        """Return the moderation dashboard snapshot."""

        return self._repository.fetch_dashboard_snapshot()
