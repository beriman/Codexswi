"""Sambatan domain services covering campaign, participation, and lifecycle."""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional

from app.services.products import ProductService, product_service


class SambatanError(Exception):
    """Base error class for Sambatan operations."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CampaignNotFound(SambatanError):
    status_code = 404


class CampaignClosed(SambatanError):
    status_code = 409


class InsufficientSlots(SambatanError):
    status_code = 409


class ParticipationNotFound(SambatanError):
    status_code = 404


class ParticipationStateInvalid(SambatanError):
    status_code = 409


class SambatanStatus(str, Enum):
    """State machine for Sambatan campaigns."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    FULL = "full"
    COMPLETED = "completed"
    FAILED = "failed"


class ParticipationStatus(str, Enum):
    """State transitions for individual participants."""

    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class SambatanAuditLog:
    """Structured log entry for lifecycle transitions."""

    campaign_id: str
    event: str
    timestamp: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SambatanParticipant:
    """Represents a participant in a Sambatan campaign."""

    id: str
    campaign_id: str
    user_id: str
    quantity: int
    status: ParticipationStatus
    joined_at: datetime
    updated_at: datetime
    shipping_address: str
    note: Optional[str] = None


@dataclass
class SambatanCampaign:
    """Aggregate root storing campaign status and counters."""

    id: str
    product_id: str
    title: str
    total_slots: int
    price_per_slot: int
    deadline: datetime
    status: SambatanStatus
    created_at: datetime
    updated_at: datetime
    slots_taken: int = 0
    payout_released: bool = False

    def slots_remaining(self) -> int:
        return max(self.total_slots - self.slots_taken, 0)

    def progress_percent(self) -> int:
        if self.total_slots == 0:
            return 0
        return min(int((self.slots_taken / self.total_slots) * 100), 100)


class SambatanService:
    """Coordinator for Sambatan campaign logic."""

    def __init__(self, catalog_service: ProductService | None = None) -> None:
        self._product_service = catalog_service or product_service
        self._campaigns: Dict[str, SambatanCampaign] = {}
        self._participants: Dict[str, SambatanParticipant] = {}
        self._campaign_participants: Dict[str, List[str]] = {}
        self._audit_logs: List[SambatanAuditLog] = []
        self._lock = threading.Lock()

    # Campaign management -------------------------------------------------
    def create_campaign(
        self,
        *,
        product_id: str,
        title: str,
        total_slots: int,
        price_per_slot: int,
        deadline: datetime,
        now: Optional[datetime] = None,
    ) -> SambatanCampaign:
        now = now or datetime.utcnow()

        product = self._product_service.get_product(product_id)
        if not product.is_sambatan_enabled:
            raise SambatanError("Produk belum diaktifkan untuk Sambatan.")

        if total_slots <= 0:
            raise SambatanError("Total slot harus lebih dari 0.")
        if price_per_slot <= 0:
            raise SambatanError("Harga per slot harus lebih dari 0.")
        if deadline <= now:
            raise SambatanError("Deadline kampanye harus di masa depan.")

        campaign_id = secrets.token_urlsafe(10)
        campaign = SambatanCampaign(
            id=campaign_id,
            product_id=product.id,
            title=title.strip(),
            total_slots=total_slots,
            price_per_slot=price_per_slot,
            deadline=deadline,
            status=SambatanStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        self._campaigns[campaign_id] = campaign
        self._campaign_participants[campaign_id] = []
        self._log(campaign_id, "campaign_created", now, {"title": campaign.title})
        return campaign

    def get_campaign(self, campaign_id: str) -> SambatanCampaign:
        try:
            return self._campaigns[campaign_id]
        except KeyError as exc:
            raise CampaignNotFound("Kampanye sambatan tidak ditemukan.") from exc

    def list_campaigns(self) -> Iterable[SambatanCampaign]:
        return self._campaigns.values()

    # Participation -------------------------------------------------------
    def join_campaign(
        self,
        *,
        campaign_id: str,
        user_id: str,
        quantity: int,
        shipping_address: str,
        note: str | None = None,
        now: Optional[datetime] = None,
    ) -> SambatanParticipant:
        now = now or datetime.utcnow()

        with self._lock:
            campaign = self.get_campaign(campaign_id)
            if campaign.status not in {SambatanStatus.ACTIVE}:
                raise CampaignClosed("Kampanye tidak menerima partisipan baru.")
            if now > campaign.deadline:
                raise CampaignClosed("Deadline kampanye telah berakhir.")
            if quantity <= 0:
                raise SambatanError("Minimal 1 slot per partisipasi.")
            if quantity > campaign.slots_remaining():
                raise InsufficientSlots("Slot sambatan tidak mencukupi.")

            participant_id = secrets.token_urlsafe(10)
            participant = SambatanParticipant(
                id=participant_id,
                campaign_id=campaign_id,
                user_id=user_id,
                quantity=quantity,
                status=ParticipationStatus.RESERVED,
                joined_at=now,
                updated_at=now,
                shipping_address=shipping_address,
                note=note,
            )

            self._participants[participant_id] = participant
            self._campaign_participants[campaign_id].append(participant_id)
            campaign.slots_taken += quantity
            campaign.updated_at = now

            if campaign.slots_taken >= campaign.total_slots:
                campaign.status = SambatanStatus.FULL
                self._log(campaign_id, "campaign_full", now, {"slots_taken": str(campaign.slots_taken)})

            self._log(
                campaign_id,
                "participant_joined",
                now,
                {"participant_id": participant_id, "quantity": str(quantity)},
            )

        return participant

    def cancel_participation(
        self,
        *,
        participation_id: str,
        reason: str | None = None,
        now: Optional[datetime] = None,
    ) -> SambatanParticipant:
        now = now or datetime.utcnow()

        with self._lock:
            participant = self._get_participation(participation_id)
            if participant.status is not ParticipationStatus.RESERVED:
                raise ParticipationStateInvalid("Partisipasi tidak dapat dibatalkan pada status saat ini.")

            campaign = self.get_campaign(participant.campaign_id)
            participant.status = ParticipationStatus.CANCELLED
            participant.updated_at = now
            campaign.slots_taken = max(campaign.slots_taken - participant.quantity, 0)
            campaign.updated_at = now
            if campaign.status is SambatanStatus.FULL and campaign.slots_remaining() > 0:
                campaign.status = SambatanStatus.ACTIVE

            self._log(
                campaign.id,
                "participant_cancelled",
                now,
                {"participant_id": participant.id, "reason": reason or ""},
            )
        return participant

    def confirm_participation(
        self,
        *,
        participation_id: str,
        now: Optional[datetime] = None,
    ) -> SambatanParticipant:
        now = now or datetime.utcnow()

        participant = self._get_participation(participation_id)
        if participant.status is not ParticipationStatus.RESERVED:
            raise ParticipationStateInvalid("Konfirmasi hanya untuk partisipan aktif.")

        participant.status = ParticipationStatus.CONFIRMED
        participant.updated_at = now
        self._log(
            participant.campaign_id,
            "participant_confirmed",
            now,
            {"participant_id": participant.id},
        )
        return participant

    def list_participants(self, campaign_id: str) -> List[SambatanParticipant]:
        self.get_campaign(campaign_id)
        ids = self._campaign_participants.get(campaign_id, [])
        return [self._participants[pid] for pid in ids]

    # Lifecycle -----------------------------------------------------------
    def run_lifecycle(self, *, now: Optional[datetime] = None) -> List[SambatanAuditLog]:
        now = now or datetime.utcnow()
        transitions: List[SambatanAuditLog] = []

        for campaign in list(self._campaigns.values()):
            previous_status = campaign.status
            if campaign.status in {SambatanStatus.COMPLETED, SambatanStatus.FAILED}:
                continue

            if campaign.status is SambatanStatus.FULL:
                self._complete_campaign(campaign, now)
            elif now > campaign.deadline:
                if campaign.slots_taken >= campaign.total_slots:
                    self._complete_campaign(campaign, now)
                else:
                    self._fail_campaign(campaign, now)

            if campaign.status is not previous_status:
                transitions.append(self._audit_logs[-1])

        return transitions

    def get_audit_logs(self, campaign_id: Optional[str] = None) -> List[SambatanAuditLog]:
        if campaign_id is None:
            return list(self._audit_logs)
        return [log for log in self._audit_logs if log.campaign_id == campaign_id]

    # Dashboard -----------------------------------------------------------
    def get_dashboard_summary(self) -> Dict[str, int]:
        total_campaigns = len(self._campaigns)
        active = len([c for c in self._campaigns.values() if c.status is SambatanStatus.ACTIVE])
        full = len([c for c in self._campaigns.values() if c.status is SambatanStatus.FULL])
        completed = len([c for c in self._campaigns.values() if c.status is SambatanStatus.COMPLETED])
        failed = len([c for c in self._campaigns.values() if c.status is SambatanStatus.FAILED])
        slots_taken = sum(c.slots_taken for c in self._campaigns.values())

        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active,
            "full_campaigns": full,
            "completed_campaigns": completed,
            "failed_campaigns": failed,
            "total_slots_taken": slots_taken,
        }

    # Internal helpers ----------------------------------------------------
    def _complete_campaign(self, campaign: SambatanCampaign, now: datetime) -> None:
        if campaign.status is SambatanStatus.COMPLETED:
            return

        campaign.status = SambatanStatus.COMPLETED
        campaign.updated_at = now
        for participant in self.list_participants(campaign.id):
            if participant.status is ParticipationStatus.RESERVED:
                participant.status = ParticipationStatus.CONFIRMED
                participant.updated_at = now
        self._log(campaign.id, "campaign_completed", now, {"slots_taken": str(campaign.slots_taken)})

    def _fail_campaign(self, campaign: SambatanCampaign, now: datetime) -> None:
        campaign.status = SambatanStatus.FAILED
        campaign.updated_at = now
        for participant in self.list_participants(campaign.id):
            if participant.status in {ParticipationStatus.RESERVED, ParticipationStatus.CONFIRMED}:
                participant.status = ParticipationStatus.REFUNDED
                participant.updated_at = now
        self._log(campaign.id, "campaign_failed", now, {"slots_taken": str(campaign.slots_taken)})

    def _get_participation(self, participation_id: str) -> SambatanParticipant:
        try:
            return self._participants[participation_id]
        except KeyError as exc:
            raise ParticipationNotFound("Partisipan tidak ditemukan.") from exc

    def _log(self, campaign_id: str, event: str, timestamp: datetime, metadata: Dict[str, str]) -> None:
        self._audit_logs.append(
            SambatanAuditLog(
                campaign_id=campaign_id,
                event=event,
                timestamp=timestamp,
                metadata=metadata,
            )
        )


class SambatanLifecycleService:
    """Scheduler-friendly wrapper for lifecycle transitions."""

    def __init__(self, sambatan_service: SambatanService | None = None) -> None:
        self._sambatan_service = sambatan_service or sambatan_service
        self._last_run: Optional[datetime] = None

    def run(self, *, now: Optional[datetime] = None) -> List[SambatanAuditLog]:
        now = now or datetime.utcnow()
        transitions = self._sambatan_service.run_lifecycle(now=now)
        self._last_run = now
        return transitions

    @property
    def last_run(self) -> Optional[datetime]:
        return self._last_run


sambatan_service = SambatanService()
"""Singleton instance shared by routers and tests."""

sambatan_lifecycle_service = SambatanLifecycleService(sambatan_service)
"""Lifecycle helper to mimic background scheduler behaviour."""

