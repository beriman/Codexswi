"""Demo data provider for the moderation, admin, and curator dashboard."""

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
    brand_slug: str
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


class ModerationDashboardService:
    """Encapsulates demo data to drive the moderation dashboard template."""

    def __init__(self) -> None:
        self._persona = {
            "name": "Arif Santoso",
            "role": "Admin Utama Moderasi",
            "mission": "Pantau antrian, distribusi tugas, dan kebijakan moderasi dalam satu layar.",
            "shift": "Shift Pagi • 07.00 - 15.00 WIB",
            "date": "Selasa, 14 Mei 2024",
            "focus": "Prioritaskan eskalasi tingkat kritis dan onboarding dua moderator baru.",
            "acknowledgement": "3 kebijakan baru belum dikonfirmasi oleh 4 anggota tim.",
        }

        self._kpis = [
            ModerationKPI(
                label="Laporan Prioritas Tinggi",
                value="12",
                delta="4 overdue > 4 jam",
                tone="warning",
            ),
            ModerationKPI(
                label="Aktivasi Moderator Minggu Ini",
                value="5/7 selesai",
                delta="2 masih menunggu pelatihan",
                tone="info",
            ),
            ModerationKPI(
                label="Akurasi Kurasi (7 hari)",
                value="92%",
                delta="+3% dari baseline",
                tone="success",
            ),
            ModerationKPI(
                label="Pelanggaran Berulang",
                value="-28%",
                delta="vs bulan lalu",
                tone="positive",
            ),
        ]

        self._alerts = [
            ModerationAlert(
                title="Eskalasi Urgensi Merah",
                description="Laporan #PR-9821 (penipuan pembayaran) belum direspon selama 3 jam.",
                severity="kritis",
                timestamp="09:42 WIB",
            ),
            ModerationAlert(
                title="Audit Quality Lead",
                description="Quality Lead meminta sampel 10 kasus kurasi kampanye Ramadhan.",
                severity="penting",
                timestamp="08:55 WIB",
            ),
            ModerationAlert(
                title="Onboarding Moderator",
                description="Undangan ke rani@marketplace.id kadaluwarsa dalam 6 jam.",
                severity="pengingat",
                timestamp="07:10 WIB",
            ),
        ]

        self._team_members = [
            TeamMemberSummary(
                name="Nadia Putri",
                role="Moderator Senior",
                status="Sedang mengaudit",
                active_cases=6,
                last_active="2 menit lalu",
                shift="Pagi",
            ),
            TeamMemberSummary(
                name="Dimas Ardi",
                role="Moderator",
                status="Menangani tiket prioritas",
                active_cases=4,
                last_active="Baru saja",
                shift="Pagi",
            ),
            TeamMemberSummary(
                name="Sela Wiryawan",
                role="Kurator Brand",
                status="Review kampanye",
                active_cases=3,
                last_active="10 menit lalu",
                shift="Siang",
            ),
            TeamMemberSummary(
                name="Grace Halim",
                role="Quality Lead",
                status="Sampling audit",
                active_cases=2,
                last_active="15 menit lalu",
                shift="Fleksibel",
            ),
        ]

        self._pending_invites = [
            PendingInvitation(
                email="rani@marketplace.id",
                role="Moderator",
                sent_at="13 Mei 2024 • 11:15",
                expires_at="Hari ini, 17:15",
            ),
            PendingInvitation(
                email="bintang@marketplace.id",
                role="Kurator",
                sent_at="13 Mei 2024 • 09:48",
                expires_at="15 Mei 2024",
            ),
        ]

        self._audit_trail = [
            AuditTrailEntry(
                time="09:35",
                actor="Arif",
                action="Mengubah SOP validasi bukti level 2 menjadi wajib verifikasi ganda.",
            ),
            AuditTrailEntry(
                time="08:12",
                actor="Nadia",
                action="Menutup laporan #PR-9712 (konten SARA) dengan tindakan suspend 7 hari.",
            ),
            AuditTrailEntry(
                time="07:55",
                actor="Sela",
                action='Mengeskalasi brand "Aurora Glow" ke admin karena skor risiko tinggi.',
            ),
        ]

        self._report_tickets = [
            ReportTicket(
                ticket_id="#PR-9821",
                category="Transaksi",
                priority="Merah",
                status="Menunggu admin",
                sla_remaining="-01:12",
                assigned_to="Arif",
                source="Komunitas",
            ),
            ReportTicket(
                ticket_id="#PR-9827",
                category="Konten",
                priority="Kuning",
                status="Dalam review",
                sla_remaining="00:45",
                assigned_to="Dimas",
                source="AI signal",
            ),
            ReportTicket(
                ticket_id="#PR-9819",
                category="Seller",
                priority="Hijau",
                status="Butuh klarifikasi",
                sla_remaining="04:20",
                assigned_to="Nadia",
                source="Internal QA",
            ),
            ReportTicket(
                ticket_id="#PR-9805",
                category="Pembeli",
                priority="Kuning",
                status="Menunggu bukti",
                sla_remaining="02:55",
                assigned_to="Belum ditetapkan",
                source="Pelapor premium",
            ),
        ]

        self._report_summary = [
            {"label": "Total antrean", "value": "86", "tone": "info"},
            {"label": "Over SLA", "value": "9", "tone": "danger"},
            {"label": "Butuh eskalasi", "value": "5", "tone": "warning"},
            {"label": "Mode fokus aktif", "value": "3 moderator", "tone": "primary"},
        ]

        self._curation_submissions = [
            CurationSubmission(
                brand="Aurora Glow",
                brand_slug="aurora-glow",
                submission_type="Pengajuan Brand",
                owner="Amelia R.",
                status="Pending Review",
                updated="23 menit lalu",
                notes="Perlu verifikasi SIUP & legalitas distributor.",
            ),
            CurationSubmission(
                brand="Rantau Craft",
                brand_slug="rantau-craft",
                submission_type="Kampanye",
                owner="Galih P.",
                status="Perlu Revisi",
                updated="1 jam lalu",
                notes="Foto hero tidak sesuai panduan, minta versi ulang.",
            ),
            CurationSubmission(
                brand="Laguna Living",
                brand_slug="laguna-living",
                submission_type="Produk Baru",
                owner="Intan M.",
                status="Approved",
                updated="Kemarin",
                notes="Produk otomatis aktif karena brand sudah terverifikasi.",
            ),
        ]

        self._curation_summary = [
            {"label": "Pengajuan baru", "value": "18", "tone": "primary"},
            {"label": "Brand high risk", "value": "3", "tone": "danger"},
            {"label": "Butuh revisi", "value": "7", "tone": "warning"},
            {"label": "Verifikasi otomatis", "value": "42 produk", "tone": "success"},
        ]

        self._checklist_highlights = [
            "Verifikasi legalitas brand minimal 2 dokumen valid.",
            "Checklist foto produk wajib resolusi > 1200px.",
            "Pastikan riwayat pelanggaran brand < 2 dalam 90 hari.",
        ]

        self._insights = [
            InsightTrend(
                label="Trend laporan mingguan",
                current="+18%",
                change="Lonjakan dari kategori transaksi",
                tone="warning",
            ),
            InsightTrend(
                label="Kurasi disetujui",
                current="74%",
                change="Stabil dibanding minggu lalu",
                tone="info",
            ),
            InsightTrend(
                label="SLA 4 jam terpenuhi",
                current="91%",
                change="Target minimal 90% terpenuhi",
                tone="success",
            ),
        ]

        self._heatmap = [
            HeatmapSlot(label="07.00-09.00", load="78%", state="padat"),
            HeatmapSlot(label="09.00-11.00", load="95%", state="kritikal"),
            HeatmapSlot(label="11.00-13.00", load="68%", state="stabil"),
            HeatmapSlot(label="13.00-15.00", load="54%", state="rendah"),
        ]

        self._violations = [
            {"category": "Penipuan pembayaran", "count": 21},
            {"category": "Konten SARA", "count": 15},
            {"category": "Pelanggaran hak cipta", "count": 11},
        ]

        self._team_productivity = [
            {"name": "Nadia", "resolved": 18, "accuracy": "94%"},
            {"name": "Dimas", "resolved": 15, "accuracy": "89%"},
            {"name": "Sela", "resolved": 12, "accuracy": "93%"},
        ]

        self._policies = [
            PolicyUpdate(
                title="SOP Verifikasi Pembayaran",
                version="v2.1",
                updated_at="13 Mei 2024",
                owner="Arif",
                tags=["transaksi", "compliance"],
            ),
            PolicyUpdate(
                title="Panduan Konten Sensitif",
                version="v1.4",
                updated_at="10 Mei 2024",
                owner="Nadia",
                tags=["konten", "komunitas"],
            ),
            PolicyUpdate(
                title="Checklist Kurasi Brand Premium",
                version="v0.9",
                updated_at="8 Mei 2024",
                owner="Sela",
                tags=["kurasi", "brand"],
            ),
        ]

        self._templates = [
            {
                "name": "Template konfirmasi bukti tambahan",
                "usage": "Moderator",
                "updated_at": "Kemarin",
            },
            {
                "name": "Template permintaan revisi brand",
                "usage": "Kurator",
                "updated_at": "2 hari lalu",
            },
            {
                "name": "Template eskalasi ke legal",
                "usage": "Admin",
                "updated_at": "Minggu lalu",
            },
        ]

        self._automation_rules = [
            "Laporan prioritas merah tanpa respon >2 jam otomatis eskalasi ke admin.",
            "Brand dengan skor risiko > 70 dikirim ke Quality Lead untuk audit.",
            "3 pelanggaran serupa dalam 30 hari memicu suspend sementara 48 jam.",
        ]

        self._help_resources = [
            HelpResource(
                title="Panduan cepat eskalasi kasus penipuan",
                category="Moderator",
                format="Playbook",
                updated_at="1 minggu lalu",
            ),
            HelpResource(
                title="Checklist onboarding kurator",
                category="Kurator",
                format="Spreadsheet",
                updated_at="3 hari lalu",
            ),
            HelpResource(
                title="Video refresher audit SOP",
                category="Quality Lead",
                format="Video",
                updated_at="April 2024",
            ),
        ]

        self._contacts = [
            ContactPoint(
                name="Arif Santoso",
                role="Admin Utama",
                channel="Slack #ops-escalation",
                availability="07.00 - 21.00",
            ),
            ContactPoint(
                name="Intan Pratiwi",
                role="Legal Advisor",
                channel="legal@sensasiwangi.id",
                availability="Hari kerja",
            ),
            ContactPoint(
                name="Rudi Hartono",
                role="Quality Lead",
                channel="Ext. 8891",
                availability="09.00 - 18.00",
            ),
        ]

    def get_snapshot(self) -> dict:
        """Return the moderation dashboard snapshot."""

        return {
            "persona": self._persona,
            "kpis": self._kpis,
            "alerts": self._alerts,
            "report_summary": self._report_summary,
            "team_members": self._team_members,
            "pending_invites": self._pending_invites,
            "audit_trail": self._audit_trail,
            "report_tickets": self._report_tickets,
            "curation_summary": self._curation_summary,
            "curation_submissions": self._curation_submissions,
            "checklist_highlights": self._checklist_highlights,
            "insights": self._insights,
            "heatmap": self._heatmap,
            "violations": self._violations,
            "team_productivity": self._team_productivity,
            "policies": self._policies,
            "templates": self._templates,
            "automation_rules": self._automation_rules,
            "help_resources": self._help_resources,
            "contacts": self._contacts,
        }


moderation_dashboard_service = ModerationDashboardService()
