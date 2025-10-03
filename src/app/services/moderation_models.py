"""Shared dataclasses for the moderation dashboard domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ModerationKPI:
    """Headline metric surfaced in the overview hero."""

    label: str
    value: str
    delta: str
    tone: str


@dataclass(frozen=True)
class ModerationAlert:
    """Realtime alert or escalation that needs attention."""

    title: str
    description: str
    severity: str
    timestamp: str


@dataclass(frozen=True)
class TeamMemberSummary:
    """Represents a moderator/curator/admin within the roster."""

    name: str
    role: str
    status: str
    active_cases: int
    last_active: str
    shift: str


@dataclass(frozen=True)
class PendingInvitation:
    """Invitation that is waiting for activation."""

    email: str
    role: str
    sent_at: str
    expires_at: str


@dataclass(frozen=True)
class AuditTrailEntry:
    """Audit log row for transparency and compliance."""

    time: str
    actor: str
    action: str


@dataclass(frozen=True)
class ReportTicket:
    """Queue item in the moderation pipeline."""

    ticket_id: str
    category: str
    priority: str
    status: str
    sla_remaining: str
    assigned_to: str
    source: str


@dataclass(frozen=True)
class CurationSubmission:
    """Submission tracked in the curator module."""

    brand: str
    submission_type: str
    owner: str
    status: str
    updated: str
    notes: str


@dataclass(frozen=True)
class InsightTrend:
    """Analytic trend metric."""

    label: str
    current: str
    change: str
    tone: str


@dataclass(frozen=True)
class HeatmapSlot:
    """Represents a block in the workload heatmap."""

    label: str
    load: str
    state: str


@dataclass(frozen=True)
class PolicyUpdate:
    """Policy changes that admins can audit."""

    title: str
    version: str
    updated_at: str
    owner: str
    tags: List[str]


@dataclass(frozen=True)
class HelpResource:
    """FAQ or learning material for the internal help center."""

    title: str
    category: str
    format: str
    updated_at: str


@dataclass(frozen=True)
class ContactPoint:
    """Escalation contact for the team."""

    name: str
    role: str
    channel: str
    availability: str


__all__ = [
    "ModerationKPI",
    "ModerationAlert",
    "TeamMemberSummary",
    "PendingInvitation",
    "AuditTrailEntry",
    "ReportTicket",
    "CurationSubmission",
    "InsightTrend",
    "HeatmapSlot",
    "PolicyUpdate",
    "HelpResource",
    "ContactPoint",
]
