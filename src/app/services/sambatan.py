"""Sambatan domain services with Supabase persistent storage."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional

from supabase import Client

from app.core.supabase import get_supabase_client, require_supabase
from app.services.products import ProductService, product_service


def _coerce_utc(value: Optional[datetime] = None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
    """State machine for Sambatan campaigns.
    
    Note: Database uses different enum values, we map between them.
    """

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


# Mapping between service enums and database enums
STATUS_TO_DB = {
    SambatanStatus.INACTIVE: "draft",
    SambatanStatus.ACTIVE: "active",
    SambatanStatus.FULL: "locked",
    SambatanStatus.COMPLETED: "fulfilled",
    SambatanStatus.FAILED: "expired",
}

DB_TO_STATUS = {v: k for k, v in STATUS_TO_DB.items()}

PARTICIPANT_STATUS_TO_DB = {
    ParticipationStatus.RESERVED: "pending_payment",
    ParticipationStatus.CONFIRMED: "confirmed",
    ParticipationStatus.CANCELLED: "cancelled",
    ParticipationStatus.REFUNDED: "refunded",
}

DB_TO_PARTICIPANT_STATUS = {v: k for k, v in PARTICIPANT_STATUS_TO_DB.items()}


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
    """Coordinator for Sambatan campaign logic with persistent storage."""

    def __init__(
        self, 
        catalog_service: ProductService | None = None,
        db: Client | None = None
    ) -> None:
        self._product_service = catalog_service or product_service
        self._db = db

    def _get_db(self) -> Client:
        """Get database client, using provided or requiring supabase."""
        if self._db is not None:
            return self._db
        return require_supabase()

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
        now = _coerce_utc(now)
        deadline = _coerce_utc(deadline)

        product = self._product_service.get_product(product_id)
        if not product.is_sambatan_enabled:
            raise SambatanError("Produk belum diaktifkan untuk Sambatan.")

        if total_slots <= 0:
            raise SambatanError("Total slot harus lebih dari 0.")
        if price_per_slot <= 0:
            raise SambatanError("Harga per slot harus lebih dari 0.")
        if deadline <= now:
            raise SambatanError("Deadline kampanye harus di masa depan.")

        db = self._get_db()
        
        # Create campaign in database
        campaign_data = {
            'product_id': product_id,
            'title': title.strip(),
            'status': STATUS_TO_DB[SambatanStatus.ACTIVE],
            'total_slots': total_slots,
            'filled_slots': 0,
            'slot_price': float(price_per_slot),
            'deadline': deadline.isoformat(),
        }
        
        result = db.table('sambatan_campaigns').insert(campaign_data).execute()
        campaign_row = result.data[0]
        
        # Create audit log
        self._log(campaign_row['id'], "campaign_created", now, {"title": title.strip()})
        
        return self._map_campaign(campaign_row)

    def get_campaign(self, campaign_id: str) -> SambatanCampaign:
        db = self._get_db()
        result = db.table('sambatan_campaigns').select('*').eq('id', campaign_id).execute()
        
        if not result.data:
            raise CampaignNotFound("Kampanye sambatan tidak ditemukan.")
        
        return self._map_campaign(result.data[0])

    def list_campaigns(self) -> Iterable[SambatanCampaign]:
        db = self._get_db()
        result = db.table('sambatan_campaigns').select('*').order('created_at', desc=True).execute()
        return [self._map_campaign(row) for row in result.data]

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
        now = _coerce_utc(now)
        db = self._get_db()

        # Get campaign and validate
        campaign = self.get_campaign(campaign_id)
        if campaign.status not in {SambatanStatus.ACTIVE}:
            raise CampaignClosed("Kampanye tidak menerima partisipan baru.")
        if now > campaign.deadline:
            raise CampaignClosed("Deadline kampanye telah berakhir.")
        if quantity <= 0:
            raise SambatanError("Minimal 1 slot per partisipasi.")
        if quantity > campaign.slots_remaining():
            raise InsufficientSlots("Slot sambatan tidak mencukupi.")

        # Atomically reserve slots using database function
        try:
            db.rpc('reserve_sambatan_slots', {
                'p_campaign_id': campaign_id,
                'p_slot_count': quantity
            }).execute()
        except Exception as e:
            if 'Insufficient slots' in str(e):
                raise InsufficientSlots("Slot sambatan tidak mencukupi.")
            elif 'Campaign is not active' in str(e):
                raise CampaignClosed("Kampanye tidak menerima partisipan baru.")
            raise SambatanError(f"Gagal mereservasi slot: {str(e)}")
        
        # Create participant
        participant_data = {
            'campaign_id': campaign_id,
            'profile_id': user_id,
            'slot_count': quantity,
            'contribution_amount': float(quantity * campaign.price_per_slot),
            'status': PARTICIPANT_STATUS_TO_DB[ParticipationStatus.RESERVED],
            'notes': note,
            'joined_at': now.isoformat(),
        }
        
        result = db.table('sambatan_participants').insert(participant_data).execute()
        participant_row = result.data[0]
        
        # Check if campaign is now full
        updated_campaign = self.get_campaign(campaign_id)
        if updated_campaign.status == SambatanStatus.FULL:
            self._log(campaign_id, "campaign_full", now, {"slots_taken": str(updated_campaign.slots_taken)})
        
        # Log participation
        self._log(
            campaign_id,
            "participant_joined",
            now,
            {"participant_id": participant_row['id'], "quantity": str(quantity)},
        )

        # Map participant with shipping address from notes
        participant_row['shipping_address'] = shipping_address
        return self._map_participant(participant_row)

    def cancel_participation(
        self,
        *,
        participation_id: str,
        reason: str | None = None,
        now: Optional[datetime] = None,
    ) -> SambatanParticipant:
        now = _coerce_utc(now)
        db = self._get_db()

        participant = self._get_participation(participation_id)
        if participant.status is not ParticipationStatus.RESERVED:
            raise ParticipationStateInvalid("Partisipasi tidak dapat dibatalkan pada status saat ini.")

        campaign = self.get_campaign(participant.campaign_id)
        
        # Update participant status
        db.table('sambatan_participants').update({
            'status': PARTICIPANT_STATUS_TO_DB[ParticipationStatus.CANCELLED],
            'cancelled_at': now.isoformat(),
        }).eq('id', participation_id).execute()
        
        # Atomically release slots using database function
        try:
            db.rpc('release_sambatan_slots', {
                'p_campaign_id': campaign.id,
                'p_slot_count': participant.quantity
            }).execute()
        except Exception as e:
            raise SambatanError(f"Gagal melepas slot: {str(e)}")
        
        # Log cancellation
        self._log(
            campaign.id,
            "participant_cancelled",
            now,
            {"participant_id": participant.id, "reason": reason or ""},
        )
        
        participant.status = ParticipationStatus.CANCELLED
        participant.updated_at = now
        return participant

    def confirm_participation(
        self,
        *,
        participation_id: str,
        now: Optional[datetime] = None,
    ) -> SambatanParticipant:
        now = _coerce_utc(now)
        db = self._get_db()

        participant = self._get_participation(participation_id)
        if participant.status is not ParticipationStatus.RESERVED:
            raise ParticipationStateInvalid("Konfirmasi hanya untuk partisipan aktif.")

        # Update participant status
        db.table('sambatan_participants').update({
            'status': PARTICIPANT_STATUS_TO_DB[ParticipationStatus.CONFIRMED],
            'confirmed_at': now.isoformat(),
        }).eq('id', participation_id).execute()
        
        self._log(
            participant.campaign_id,
            "participant_confirmed",
            now,
            {"participant_id": participant.id},
        )
        
        participant.status = ParticipationStatus.CONFIRMED
        participant.updated_at = now
        return participant

    def list_participants(self, campaign_id: str) -> List[SambatanParticipant]:
        self.get_campaign(campaign_id)  # Validate campaign exists
        db = self._get_db()
        
        result = db.table('sambatan_participants').select('*').eq('campaign_id', campaign_id).execute()
        return [self._map_participant(row) for row in result.data]

    # Lifecycle -----------------------------------------------------------
    def run_lifecycle(self, *, now: Optional[datetime] = None) -> List[SambatanAuditLog]:
        now = _coerce_utc(now)
        transitions: List[SambatanAuditLog] = []
        db = self._get_db()

        # Get all active campaigns
        result = db.table('sambatan_campaigns').select('*').in_(
            'status',
            [STATUS_TO_DB[SambatanStatus.ACTIVE], STATUS_TO_DB[SambatanStatus.FULL]]
        ).execute()

        for campaign_row in result.data:
            campaign = self._map_campaign(campaign_row)
            previous_status = campaign.status

            if campaign.status is SambatanStatus.FULL:
                self._complete_campaign(campaign, now)
                transitions.append(self._audit_logs_cache[-1] if hasattr(self, '_audit_logs_cache') else 
                                 SambatanAuditLog(campaign.id, "campaign_completed", now, {}))
            elif now > campaign.deadline:
                if campaign.slots_taken >= campaign.total_slots:
                    self._complete_campaign(campaign, now)
                    transitions.append(SambatanAuditLog(campaign.id, "campaign_completed", now, {}))
                else:
                    self._fail_campaign(campaign, now)
                    transitions.append(SambatanAuditLog(campaign.id, "campaign_failed", now, {}))

        return transitions

    def get_audit_logs(self, campaign_id: Optional[str] = None) -> List[SambatanAuditLog]:
        db = self._get_db()
        
        query = db.table('sambatan_audit_logs').select('*').order('created_at', desc=True)
        if campaign_id:
            query = query.eq('campaign_id', campaign_id)
        
        result = query.execute()
        return [self._map_audit_log(row) for row in result.data]

    # Dashboard -----------------------------------------------------------
    def get_dashboard_summary(self) -> Dict[str, int]:
        db = self._get_db()
        
        result = db.table('sambatan_campaigns').select('status, filled_slots').execute()
        
        campaigns = result.data
        total_campaigns = len(campaigns)
        active = len([c for c in campaigns if DB_TO_STATUS.get(c['status']) == SambatanStatus.ACTIVE])
        full = len([c for c in campaigns if DB_TO_STATUS.get(c['status']) == SambatanStatus.FULL])
        completed = len([c for c in campaigns if DB_TO_STATUS.get(c['status']) == SambatanStatus.COMPLETED])
        failed = len([c for c in campaigns if DB_TO_STATUS.get(c['status']) == SambatanStatus.FAILED])
        slots_taken = sum(c['filled_slots'] for c in campaigns)

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
        
        db = self._get_db()

        # Use atomic database function to complete campaign
        try:
            db.rpc('complete_sambatan_campaign', {
                'p_campaign_id': campaign.id
            }).execute()
        except Exception as e:
            raise SambatanError(f"Gagal menyelesaikan kampanye: {str(e)}")
        
        self._log(campaign.id, "campaign_completed", now, {"slots_taken": str(campaign.slots_taken)})

    def _fail_campaign(self, campaign: SambatanCampaign, now: datetime) -> None:
        db = self._get_db()
        
        # Use atomic database function to fail campaign
        try:
            db.rpc('fail_sambatan_campaign', {
                'p_campaign_id': campaign.id
            }).execute()
        except Exception as e:
            raise SambatanError(f"Gagal membatalkan kampanye: {str(e)}")
        
        self._log(campaign.id, "campaign_failed", now, {"slots_taken": str(campaign.slots_taken)})

    def _get_participation(self, participation_id: str) -> SambatanParticipant:
        db = self._get_db()
        result = db.table('sambatan_participants').select('*').eq('id', participation_id).execute()
        
        if not result.data:
            raise ParticipationNotFound("Partisipan tidak ditemukan.")
        
        return self._map_participant(result.data[0])

    def _log(self, campaign_id: str, event: str, timestamp: datetime, metadata: Dict[str, str]) -> None:
        db = self._get_db()
        
        log_data = {
            'campaign_id': campaign_id,
            'event': event,
            'metadata': metadata,
            'created_at': timestamp.isoformat(),
        }
        
        db.table('sambatan_audit_logs').insert(log_data).execute()

    # Mapping helpers -----------------------------------------------------
    def _map_campaign(self, row: Dict) -> SambatanCampaign:
        """Map database row to SambatanCampaign dataclass."""
        return SambatanCampaign(
            id=row['id'],
            product_id=row['product_id'],
            title=row.get('title', ''),
            total_slots=row['total_slots'],
            price_per_slot=int(row['slot_price']),
            deadline=datetime.fromisoformat(row['deadline']) if row.get('deadline') else datetime.now(UTC),
            status=DB_TO_STATUS.get(row['status'], SambatanStatus.INACTIVE),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            slots_taken=row['filled_slots'],
            payout_released=False,
        )

    def _map_participant(self, row: Dict) -> SambatanParticipant:
        """Map database row to SambatanParticipant dataclass."""
        return SambatanParticipant(
            id=row['id'],
            campaign_id=row['campaign_id'],
            user_id=row.get('profile_id', ''),
            quantity=row['slot_count'],
            status=DB_TO_PARTICIPANT_STATUS.get(row['status'], ParticipationStatus.RESERVED),
            joined_at=datetime.fromisoformat(row['joined_at']),
            updated_at=datetime.fromisoformat(row.get('confirmed_at') or row.get('cancelled_at') or row['joined_at']),
            shipping_address=row.get('shipping_address', row.get('notes', '')),
            note=row.get('notes'),
        )

    def _map_audit_log(self, row: Dict) -> SambatanAuditLog:
        """Map database row to SambatanAuditLog dataclass."""
        return SambatanAuditLog(
            campaign_id=row['campaign_id'],
            event=row['event'],
            timestamp=datetime.fromisoformat(row['created_at']),
            metadata=row.get('metadata', {}),
        )


class SambatanLifecycleService:
    """Scheduler-friendly wrapper for lifecycle transitions."""

    def __init__(self, sambatan_service: SambatanService | None = None) -> None:
        self._sambatan_service = sambatan_service or SambatanService()
        self._last_run: Optional[datetime] = None

    def run(self, *, now: Optional[datetime] = None) -> List[SambatanAuditLog]:
        now = _coerce_utc(now)
        transitions = self._sambatan_service.run_lifecycle(now=now)
        self._last_run = now
        return transitions

    @property
    def last_run(self) -> Optional[datetime]:
        return self._last_run


# Singleton instances - will use Supabase when available
sambatan_service = SambatanService()
"""Singleton instance shared by routers and tests."""

sambatan_lifecycle_service = SambatanLifecycleService(sambatan_service)
"""Lifecycle helper to mimic background scheduler behaviour."""
