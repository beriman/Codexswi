"""Service layer providing demo data for the brand owner dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List


@dataclass(frozen=True)
class DashboardKPI:
    """Represents a key metric surfaced on the dashboard hero area."""

    label: str
    value: str
    delta_label: str
    is_positive: bool


@dataclass(frozen=True)
class OrderStatusSummary:
    """Aggregated counts for the order status overview chips."""

    label: str
    count: int
    tone: str


@dataclass(frozen=True)
class DashboardNotification:
    """Important alert surfaced to the operator."""

    category: str
    message: str
    urgency: str


@dataclass(frozen=True)
class ManagedProduct:
    """Simplified representation of a product row."""

    name: str
    status: str
    stock_level: str
    price: str
    updated: str
    sku: str


@dataclass(frozen=True)
class ManagedOrder:
    """Recent order entries shown in the order table."""

    invoice: str
    customer: str
    items: int
    total: str
    status: str
    updated: str


@dataclass(frozen=True)
class PromotionSnapshot:
    """Short summary of an active promotion or campaign."""

    name: str
    status: str
    goal: str
    progress_percent: int
    period: str


@dataclass(frozen=True)
class VerificationStep:
    """Individual step of the brand verification workflow."""

    title: str
    status: str
    description: str


@dataclass(frozen=True)
class VerificationDocument:
    """Document checklist item for verification."""

    name: str
    status: str
    note: str | None = None


@dataclass(frozen=True)
class TeamMember:
    """Represents a collaborator within the brand team."""

    name: str
    role: str
    email: str
    last_active: str
    permissions: List[str]


@dataclass(frozen=True)
class TeamInvitation:
    """Pending invitation state for collaborators."""

    email: str
    role: str
    sent_at: str
    expires_at: str


@dataclass(frozen=True)
class ActivityLog:
    """Audit log entries for transparency."""

    timestamp: str
    actor: str
    action: str


class BrandOwnerDashboardService:
    """Encapsulates dashboard specific demo data for the brand owner persona."""

    def __init__(self) -> None:
        self._brand_profile = {
            "brand_name": "Studio Senja",
            "tagline": "Kelola katalog, pesanan, dan tim dalam satu layar.",
            "owner_name": "Ayu Prameswari",
            "sync_status": "Sinkronisasi stok terakhir 2 menit lalu",
        }

        self._kpis: List[DashboardKPI] = [
            DashboardKPI(
                label="Penjualan Bulan Ini",
                value="Rp182,4 Jt",
                delta_label="+12,4% dibanding bulan lalu",
                is_positive=True,
            ),
            DashboardKPI(
                label="Pesanan Aktif",
                value="128",
                delta_label="18 perlu tindak lanjut hari ini",
                is_positive=False,
            ),
            DashboardKPI(
                label="Rata-rata Nilai Order",
                value="Rp1,42 Jt",
                delta_label="+6,1% dalam 30 hari",
                is_positive=True,
            ),
            DashboardKPI(
                label="SKU Stok Kritis",
                value="6",
                delta_label="Segera jadwalkan restock",
                is_positive=False,
            ),
        ]

        self._order_statuses: List[OrderStatusSummary] = [
            OrderStatusSummary(label="Baru", count=24, tone="info"),
            OrderStatusSummary(label="Diproses", count=42, tone="primary"),
            OrderStatusSummary(label="Dikirim", count=51, tone="success"),
            OrderStatusSummary(label="Perlu Perhatian", count=11, tone="warning"),
        ]

        self._notifications: List[DashboardNotification] = [
            DashboardNotification(
                category="Stok",
                message="Euforia Pagi tinggal 14 botol di gudang utama.",
                urgency="Tinggi",
            ),
            DashboardNotification(
                category="Pesanan",
                message="3 pesanan pre-order melewati SLA konfirmasi 24 jam.",
                urgency="Sedang",
            ),
            DashboardNotification(
                category="Verifikasi",
                message="Kurator meminta revisi portofolio foto untuk tahap verifikasi brand.",
                urgency="Perlu Tindakan",
            ),
        ]

        self._products: List[ManagedProduct] = [
            ManagedProduct(
                name="Euforia Pagi Eau de Parfum",
                status="aktif",
                stock_level="128 unit",
                price="Rp475.000",
                updated="3 jam lalu",
                sku="STJ-EFP-50",
            ),
            ManagedProduct(
                name="Galaksi Senja Discovery Set",
                status="aktif",
                stock_level="64 set",
                price="Rp320.000",
                updated="1 hari lalu",
                sku="STJ-GS-DSC",
            ),
            ManagedProduct(
                name="Sampler Atelier Eksklusif",
                status="draft",
                stock_level="--",
                price="Rp180.000",
                updated="Menunggu foto",
                sku="STJ-SMPLR",
            ),
            ManagedProduct(
                name="Seri Kolaborasi Nusantarum x Studio Senja",
                status="pending",
                stock_level="Batch 1: 80",
                price="Rp520.000",
                updated="Butuh approval",
                sku="STJ-NUSA-01",
            ),
            ManagedProduct(
                name="Refill Base Oil 1L",
                status="arsip",
                stock_level="0",
                price="Rp850.000",
                updated="Diarsipkan 12 Mei",
                sku="STJ-RFL-1L",
            ),
        ]

        self._orders: List[ManagedOrder] = [
            ManagedOrder(
                invoice="INV-240512-9812",
                customer="Rina Maheswari",
                items=3,
                total="Rp1.420.000",
                status="Diproses",
                updated="10 menit lalu",
            ),
            ManagedOrder(
                invoice="INV-240512-9804",
                customer="Bayu Wicaksana",
                items=1,
                total="Rp475.000",
                status="Baru",
                updated="Baru masuk",
            ),
            ManagedOrder(
                invoice="INV-240511-9720",
                customer="Nadia Permata",
                items=2,
                total="Rp945.000",
                status="Dikirim",
                updated="Resi JNE 12 Mei",
            ),
            ManagedOrder(
                invoice="INV-240511-9714",
                customer="Andra Kusumah",
                items=4,
                total="Rp2.040.000",
                status="Perlu perhatian",
                updated="Komplain aroma",
            ),
        ]

        self._promotions: List[PromotionSnapshot] = [
            PromotionSnapshot(
                name="Voucher Loyalis Ramadan",
                status="Aktif",
                goal="Target Rp60 Jt",
                progress_percent=72,
                period="1-15 Ramadan",
            ),
            PromotionSnapshot(
                name="Sambatan Kolaborasi Nusantarum",
                status="Pra-launch",
                goal="150 slot kontributor",
                progress_percent=48,
                period="Draft jadwal",
            ),
            PromotionSnapshot(
                name="Bundling Discovery Set",
                status="Selesai",
                goal="Terjual 320 set",
                progress_percent=100,
                period="April 2024",
            ),
        ]

        self._verification_steps: List[VerificationStep] = [
            VerificationStep(
                title="Lengkapi Data Legal",
                status="selesai",
                description="Nomor NIB dan NPWP brand sudah diverifikasi sistem.",
            ),
            VerificationStep(
                title="Unggah Portofolio Brand",
                status="revisi",
                description="Kurator meminta tambahan dokumentasi foto workshop.",
            ),
            VerificationStep(
                title="Konfirmasi Penanggung Jawab",
                status="menunggu",
                description="Undangan tanda tangan digital dikirim ke co-founder.",
            ),
            VerificationStep(
                title="Review Kurator",
                status="menunggu",
                description="Estimasi SLA 2 hari kerja setelah dokumen lengkap.",
            ),
        ]

        self._verification_documents: List[VerificationDocument] = [
            VerificationDocument(
                name="Surat Izin Usaha",
                status="Lengkap",
            ),
            VerificationDocument(
                name="Identitas Penanggung Jawab",
                status="Lengkap",
            ),
            VerificationDocument(
                name="Portofolio Produk",
                status="Perlu revisi",
                note="Tambahkan dokumentasi proses produksi dan sertifikasi batch.",
            ),
            VerificationDocument(
                name="Sertifikat Halal / BPOM",
                status="Opsional",
                note="Upload jika tersedia untuk percepat review retail partner.",
            ),
        ]

        self._team_members: List[TeamMember] = [
            TeamMember(
                name="Ayu Prameswari",
                role="Brand Owner",
                email="ayu@studiosenja.id",
                last_active="Online",
                permissions=["Semua modul", "Kelola tim", "Akses finansial"],
            ),
            TeamMember(
                name="Rifky Hartanto",
                role="Co-founder",
                email="rifky@studiosenja.id",
                last_active="1 jam lalu",
                permissions=["Manajemen produk", "Sambatan", "Analitik"],
            ),
            TeamMember(
                name="Sari Utami",
                role="Admin Operasional",
                email="sari@studiosenja.id",
                last_active="43 menit lalu",
                permissions=["Pesanan", "Stok", "Respon pelanggan"],
            ),
            TeamMember(
                name="Galih Wibisono",
                role="Staff Warehouse",
                email="warehouse@studiosenja.id",
                last_active="2 jam lalu",
                permissions=["Update stok", "Cetak label", "Logistik"],
            ),
        ]

        self._invitations: List[TeamInvitation] = [
            TeamInvitation(
                email="keuangan@studiosenja.id",
                role="Finance Viewer",
                sent_at="12 Mei 10:20",
                expires_at="18 Mei 23:59",
            )
        ]

        self._activity_log: List[ActivityLog] = [
            ActivityLog(
                timestamp="12 Mei 09:12",
                actor="Ayu",
                action="Mengaktifkan voucher Loyalis Ramadan",
            ),
            ActivityLog(
                timestamp="11 Mei 21:45",
                actor="Sari",
                action="Memperbarui status 8 pesanan ke 'Dikirim'",
            ),
            ActivityLog(
                timestamp="11 Mei 16:05",
                actor="Rifky",
                action="Mengunggah draft portofolio verifikasi brand",
            ),
            ActivityLog(
                timestamp="10 Mei 13:22",
                actor="Galih",
                action="Menambahkan stok masuk untuk SKU STJ-EFP-50",
            ),
        ]

        self._analytics_ranges = [
            {
                "key": "7d",
                "label": "7 Hari",
                "summary": {
                    "revenue": "Rp42,8 Jt",
                    "orders": 182,
                    "avg_order": "Rp1,32 Jt",
                    "conversion": "3,8%",
                },
                "points": [12, 16, 14, 18, 21, 19, 24],
                "x_labels": ["Sel", "Rab", "Kam", "Jum", "Sab", "Min", "Sen"],
                "top_products": [
                    {"name": "Euforia Pagi", "share": "28%"},
                    {"name": "Discovery Set", "share": "22%"},
                    {"name": "Kolaborasi Nusantarum", "share": "17%"},
                ],
                "segments": [
                    {"label": "Pelanggan Baru", "value": "38%"},
                    {"label": "Pelanggan Kembali", "value": "62%"},
                ],
            },
            {
                "key": "30d",
                "label": "30 Hari",
                "summary": {
                    "revenue": "Rp182,4 Jt",
                    "orders": 712,
                    "avg_order": "Rp1,42 Jt",
                    "conversion": "4,2%",
                },
                "points": [9, 11, 12, 15, 18, 17, 19, 22, 21, 20, 24, 23, 25, 26, 28],
                "x_labels": ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15"],
                "top_products": [
                    {"name": "Euforia Pagi", "share": "31%"},
                    {"name": "Discovery Set", "share": "19%"},
                    {"name": "Refill Base Oil", "share": "12%"},
                ],
                "segments": [
                    {"label": "Jabodetabek", "value": "44%"},
                    {"label": "Jawa Tengah", "value": "23%"},
                    {"label": "Kalimantan", "value": "11%"},
                    {"label": "Sulawesi", "value": "9%"},
                ],
            },
            {
                "key": "90d",
                "label": "90 Hari",
                "summary": {
                    "revenue": "Rp512,7 Jt",
                    "orders": 1_862,
                    "avg_order": "Rp1,37 Jt",
                    "conversion": "4,0%",
                },
                "points": [6, 8, 7, 9, 11, 15, 14, 16, 18, 21, 19, 23, 24, 26, 25, 28, 30, 29, 31],
                "x_labels": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12", "W13", "W14", "W15", "W16", "W17", "W18", "W19"],
                "top_products": [
                    {"name": "Kolaborasi Nusantarum", "share": "26%"},
                    {"name": "Euforia Pagi", "share": "25%"},
                    {"name": "Discovery Set", "share": "18%"},
                ],
                "segments": [
                    {"label": "Marketplace", "value": "52%"},
                    {"label": "Sambatan", "value": "33%"},
                    {"label": "Retail Offline", "value": "15%"},
                ],
            },
        ]

        self._verification_timeline = [
            {
                "date": date(2024, 5, 9),
                "actor": "Kurator Nusantarum",
                "message": "Review awal dokumen legal selesai – menunggu unggahan portofolio.",
            },
            {
                "date": date(2024, 5, 11),
                "actor": "Ayu Prameswari",
                "message": "Mengunggah portofolio brand dan menambahkan catatan produksi.",
            },
            {
                "date": date(2024, 5, 12),
                "actor": "Kurator Nusantarum",
                "message": "Meminta revisi foto workshop dan sertifikat pelatihan staf.",
            },
        ]

    def get_kpis(self) -> Iterable[DashboardKPI]:
        return tuple(self._kpis)

    def get_order_statuses(self) -> Iterable[OrderStatusSummary]:
        return tuple(self._order_statuses)

    def get_notifications(self) -> Iterable[DashboardNotification]:
        return tuple(self._notifications)

    def get_products(self) -> Iterable[ManagedProduct]:
        return tuple(self._products)

    def get_orders(self) -> Iterable[ManagedOrder]:
        return tuple(self._orders)

    def get_promotions(self) -> Iterable[PromotionSnapshot]:
        return tuple(self._promotions)

    def get_verification_steps(self) -> Iterable[VerificationStep]:
        return tuple(self._verification_steps)

    def get_verification_documents(self) -> Iterable[VerificationDocument]:
        return tuple(self._verification_documents)

    def get_team_members(self) -> Iterable[TeamMember]:
        return tuple(self._team_members)

    def get_invitations(self) -> Iterable[TeamInvitation]:
        return tuple(self._invitations)

    def get_activity_log(self) -> Iterable[ActivityLog]:
        return tuple(self._activity_log)

    def get_analytics_ranges(self) -> Iterable[dict]:
        return tuple(self._analytics_ranges)

    def get_verification_timeline(self) -> Iterable[dict]:
        return tuple(self._verification_timeline)

    def get_snapshot(self) -> dict:
        """Return an aggregated snapshot used by the template renderer."""

        return {
            "brand_profile": self._brand_profile,
            "kpis": self.get_kpis(),
            "order_statuses": self.get_order_statuses(),
            "notifications": self.get_notifications(),
            "products": self.get_products(),
            "orders": self.get_orders(),
            "promotions": self.get_promotions(),
            "verification_steps": self.get_verification_steps(),
            "verification_documents": self.get_verification_documents(),
            "verification_timeline": self.get_verification_timeline(),
            "team_members": self.get_team_members(),
            "team_invitations": self.get_invitations(),
            "activity_log": self.get_activity_log(),
            "analytics_ranges": self.get_analytics_ranges(),
        }


brand_dashboard_service = BrandOwnerDashboardService()
"""Singleton service used by the router to populate dashboard views."""

