"""Repository layer for the moderation dashboard domain structures."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Sequence

from app.services.brands import Brand, BrandHighlight, BrandProduct, BrandService, brand_service
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
from app.services.reporting import SalesRecord, SalesReportService


class ModerationDashboardRepository:
    """Access layer aggregating data for the moderation dashboard."""

    def __init__(
        self,
        *,
        brand_source: BrandService | None = None,
        sales_source: SalesReportService | None = None,
        plan_path: Path | None = None,
    ) -> None:
        self._brand_source = brand_source or brand_service
        self._sales_source = sales_source or SalesReportService()
        self._plan_path = plan_path or Path(__file__).resolve().parents[3] / "docs" / "moderation-dashboard-plan.md"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_dashboard_snapshot(self) -> dict:
        """Compose the dashboard snapshot from upstream sources."""

        persona = self._build_persona()
        team_members = self._build_team_members()
        pending_invites = self._build_pending_invites()
        sales_records = self._load_recent_sales()

        report_tickets = self._build_report_tickets(team_members, sales_records)
        curation_submissions = self._build_curation_submissions()

        return {
            "persona": persona,
            "kpis": self._build_kpis(sales_records, pending_invites),
            "alerts": self._build_alerts(),
            "report_summary": self._build_report_summary(report_tickets),
            "team_members": team_members,
            "pending_invites": pending_invites,
            "audit_trail": self._build_audit_trail(),
            "report_tickets": report_tickets,
            "curation_summary": self._build_curation_summary(curation_submissions),
            "curation_submissions": curation_submissions,
            "checklist_highlights": self._extract_plan_bullets("## 8. KPI & Monitoring Keberhasilan"),
            "insights": self._build_insights(sales_records),
            "heatmap": self._build_heatmap(sales_records),
            "violations": self._build_violation_stats(sales_records),
            "team_productivity": self._build_team_productivity(team_members),
            "policies": self._build_policies(persona["name"]),
            "templates": self._build_templates(),
            "automation_rules": self._extract_plan_bullets("### Mekanisme Monitoring"),
            "help_resources": self._build_help_resources(),
            "contacts": self._build_contacts(team_members),
        }

    # ------------------------------------------------------------------
    # Persona & team helpers
    # ------------------------------------------------------------------
    def _build_persona(self) -> dict:
        brand = self._brand_source.get_brand("langit-senja")
        owners = brand.list_owners()
        owner = owners[0] if owners else brand.members[0]

        today = datetime.now(UTC).astimezone().strftime("%A, %d %B %Y")
        pending_invites = sum(len(b.list_pending_members()) for b in self._brand_source.list_brands())

        return {
            "name": owner.full_name,
            "role": "Admin Utama Moderasi",
            "mission": f"Sinkronkan moderasi & kurasi lintas brand seperti {brand.name} agar SLA terjaga.",
            "shift": "Shift Pagi • 07.00 - 15.00 WIB",
            "date": today,
            "focus": "Pantau eskalasi transaksi besar dan onboarding anggota komunitas terbaru.",
            "acknowledgement": f"{pending_invites} undangan tim menunggu aktivasi.",
        }

    def _build_team_members(self) -> List[TeamMemberSummary]:
        roster: List[TeamMemberSummary] = []
        shift_cycle = ["Pagi", "Siang", "Malam"]
        status_map = {
            "active": "Sedang bertugas",
            "pending": "Menunggu aktivasi",
            "inactive": "Tidak aktif",
        }

        for index, brand in enumerate(self._brand_source.list_brands()):
            for member in brand.members:
                status = status_map.get(member.status, member.status.title())
                position = len(roster)
                active_cases = 2 + (index + position) % 5
                last_active = f"{(index + position) * 3 or 1} menit lalu"
                role = "Admin" if member.role == "owner" else "Kurator" if member.role == "co-owner" else member.role.title()
                roster.append(
                    TeamMemberSummary(
                        name=member.full_name,
                        role=role,
                        status=status,
                        active_cases=active_cases,
                        last_active=last_active,
                        shift=shift_cycle[(index + position) % len(shift_cycle)],
                    )
                )

        return roster[:5]

    def _build_pending_invites(self) -> List[PendingInvitation]:
        invites: List[PendingInvitation] = []
        now = datetime.now().astimezone()
        for offset, brand in enumerate(self._brand_source.list_brands()):
            for member in brand.list_pending_members():
                sent_at = now - timedelta(hours=offset * 6)
                expires_at = sent_at + timedelta(days=1)
                invites.append(
                    PendingInvitation(
                        email=f"{member.username}@sensasiwangi.id",
                        role=member.role.title(),
                        sent_at=sent_at.strftime("%d %b %Y • %H:%M"),
                        expires_at=expires_at.strftime("%d %b %Y"),
                    )
                )

        return invites

    # ------------------------------------------------------------------
    # KPI & insight helpers
    # ------------------------------------------------------------------
    def _load_recent_sales(self) -> List[SalesRecord]:
        today = date.today()
        start = today - timedelta(days=6)
        return self._sales_source.get_sales_report(start, today)

    def _build_kpis(self, sales_records: Sequence[SalesRecord], invites: Sequence[PendingInvitation]) -> List[ModerationKPI]:
        total_amount = sum(record.total_amount for record in sales_records)
        pending = sum(1 for record in sales_records if record.status != "settled")
        avg_items = (sum(record.total_items for record in sales_records) / len(sales_records)) if sales_records else 0
        unique_customers = {record.customer_name for record in sales_records}
        transfer_orders = sum(1 for record in sales_records if record.payment_method == "transfer")

        return [
            ModerationKPI(
                label="Order 7 hari terakhir",
                value=str(len(sales_records)),
                delta=f"{pending} menunggu penyelesaian",
                tone="info",
            ),
            ModerationKPI(
                label="Total nilai transaksi",
                value=self._format_currency(total_amount),
                delta=f"{len(unique_customers)} pelanggan unik",
                tone="success" if total_amount else "info",
            ),
            ModerationKPI(
                label="Rata-rata item per order",
                value=f"{avg_items:.1f}",
                delta=f"{transfer_orders} via transfer",
                tone="primary",
            ),
            ModerationKPI(
                label="Onboarding anggota baru",
                value=f"{len(invites)} undangan",
                delta="Pantau aktivasi dalam 24 jam",
                tone="warning" if invites else "info",
            ),
        ]

    def _build_insights(self, sales_records: Sequence[SalesRecord]) -> List[InsightTrend]:
        if not sales_records:
            return []

        totals_by_day: Counter[date] = Counter()
        for record in sales_records:
            totals_by_day[record.order_date] += record.total_amount

        sorted_days = sorted(totals_by_day.keys())
        latest_day = sorted_days[-1]
        previous_day = sorted_days[-2] if len(sorted_days) > 1 else sorted_days[-1]
        latest_total = totals_by_day[latest_day]
        previous_total = totals_by_day[previous_day]
        delta = latest_total - previous_total

        avg_amount = sum(totals_by_day.values()) / len(totals_by_day)
        highest_day = max(totals_by_day, key=totals_by_day.get)

        tone = "success" if delta >= 0 else "warning"

        return [
            InsightTrend(
                label="Nilai transaksi harian",
                current=self._format_currency(latest_total),
                change=f"{self._format_currency(delta)} vs hari sebelumnya",
                tone=tone,
            ),
            InsightTrend(
                label="Rata-rata order harian",
                current=self._format_currency(avg_amount),
                change=f"Puncak di {highest_day.strftime('%d %b')}",
                tone="info",
            ),
            InsightTrend(
                label="Metode pembayaran populer",
                current=self._top_payment_method(sales_records),
                change="Optimalkan SOP verifikasi manual",
                tone="warning",
            ),
        ]

    def _build_heatmap(self, sales_records: Sequence[SalesRecord]) -> List[HeatmapSlot]:
        if not sales_records:
            return []

        totals = Counter(record.order_date.strftime("%a") for record in sales_records)
        max_total = max(totals.values()) or 1
        slots: List[HeatmapSlot] = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            if day not in totals:
                continue
            load_percent = int((totals[day] / max_total) * 100)
            state = "stabil"
            if load_percent >= 90:
                state = "kritikal"
            elif load_percent >= 70:
                state = "padat"
            elif load_percent <= 40:
                state = "rendah"
            slots.append(HeatmapSlot(label=day, load=f"{load_percent}%", state=state))

        return slots

    def _build_violation_stats(self, sales_records: Sequence[SalesRecord]) -> List[dict]:
        categories = Counter(record.payment_method for record in sales_records)
        mapping = {
            "transfer": "Verifikasi transfer",
            "virtual_account": "Virtual account",
            "ewallet": "Dompet digital",
            "cash_on_delivery": "COD",
        }
        return [
            {"category": mapping.get(method, method.title()), "count": count}
            for method, count in categories.most_common()
        ]

    # ------------------------------------------------------------------
    # Alerts & narrative helpers
    # ------------------------------------------------------------------
    def _build_alerts(self) -> List[ModerationAlert]:
        alerts: List[ModerationAlert] = []
        for highlight in self._iter_highlights():
            severity = "pengingat"
            if "Sambatan" in highlight.title:
                severity = "kritis"
            elif "Nusantarum" in highlight.title:
                severity = "penting"
            alerts.append(
                ModerationAlert(
                    title=highlight.title,
                    description=highlight.description,
                    severity=severity,
                    timestamp=highlight.timestamp,
                )
            )
        return alerts[:3]

    def _build_audit_trail(self) -> List[AuditTrailEntry]:
        entries: List[AuditTrailEntry] = []
        for index, (brand, story) in enumerate(self._iter_story_points()):
            owner = brand.list_owners()
            actor = owner[0].full_name if owner else brand.name
            time = f"{8 + index:02d}:{15 + index * 7:02d}"
            entries.append(
                AuditTrailEntry(
                    time=time,
                    actor=actor,
                    action=story,
                )
            )
        return entries[:3]

    # ------------------------------------------------------------------
    # Report & curation helpers
    # ------------------------------------------------------------------
    def _build_report_tickets(
        self,
        team_members: Sequence[TeamMemberSummary],
        sales_records: Sequence[SalesRecord],
    ) -> List[ReportTicket]:
        tickets: List[ReportTicket] = []
        assignees = [member.name for member in team_members] or ["Tim Moderasi"]

        for index, record in enumerate(sorted(sales_records, key=lambda r: r.total_amount, reverse=True)):
            priority = self._classify_priority(record.total_amount)
            status = "Menunggu admin" if record.status != "settled" else "Selesai"
            sla_remaining = "-00:45" if index == 0 and status != "Selesai" else f"0{2 + index}:30"
            tickets.append(
                ReportTicket(
                    ticket_id=record.order_id,
                    category=self._map_payment_to_category(record.payment_method),
                    priority=priority,
                    status=status,
                    sla_remaining=sla_remaining,
                    assigned_to=assignees[index % len(assignees)],
                    source=record.payment_method.replace("_", " ").title(),
                )
            )

        return tickets[:4]

    def _build_report_summary(self, report_tickets: Sequence[ReportTicket]) -> List[dict]:
        total = len(report_tickets)
        overdue = sum(1 for ticket in report_tickets if ticket.sla_remaining.startswith("-"))
        critical = sum(1 for ticket in report_tickets if ticket.priority == "Merah")
        waiting_assignment = sum(1 for ticket in report_tickets if ticket.assigned_to == "Belum ditetapkan")

        return [
            {"label": "Total antrean", "value": str(total), "tone": "info"},
            {"label": "Over SLA", "value": str(overdue), "tone": "danger"},
            {"label": "Prioritas merah", "value": str(critical), "tone": "warning"},
            {"label": "Belum ditetapkan", "value": f"{waiting_assignment} tiket", "tone": "primary"},
        ]

    def _build_curation_submissions(self) -> List[CurationSubmission]:
        submissions: List[CurationSubmission] = []
        now = datetime.now().astimezone()
        for index, (brand, product) in enumerate(self._iter_products()):
            status = "Disetujui" if brand.is_verified else "Menunggu admin"
            if product.is_sambatan:
                status = "Butuh klarifikasi"
            updated = now - timedelta(minutes=15 * (index + 1))
            notes = f"{brand.name}: {product.hero_note}"
            submissions.append(
                CurationSubmission(
                    brand=brand.name,
                    submission_type="Produk Sambatan" if product.is_sambatan else "Koleksi Brand",
                    owner=brand.list_owners()[0].full_name if brand.list_owners() else brand.name,
                    status=status,
                    updated=updated.strftime("%d %b %Y" if index > 1 else "%H:%M"),
                    notes=notes,
                )
            )
        return submissions[:3]

    def _build_curation_summary(self, submissions: Sequence[CurationSubmission]) -> List[dict]:
        totals = Counter(submission.status for submission in submissions)
        return [
            {"label": "Total pengajuan", "value": str(sum(totals.values())), "tone": "primary"},
            {"label": "Disetujui", "value": str(totals.get("Disetujui", 0)), "tone": "success"},
            {"label": "Menunggu admin", "value": str(totals.get("Menunggu admin", 0)), "tone": "info"},
            {"label": "Butuh klarifikasi", "value": str(totals.get("Butuh klarifikasi", 0)), "tone": "warning"},
        ]

    # ------------------------------------------------------------------
    # Handbook & policy helpers
    # ------------------------------------------------------------------
    def _build_team_productivity(self, team_members: Sequence[TeamMemberSummary]) -> List[dict]:
        stats = []
        for index, member in enumerate(team_members):
            resolved = 12 + index * 3
            accuracy = 90 + (index % 3) * 2
            stats.append(
                {"name": member.name.split()[0], "resolved": resolved, "accuracy": f"{accuracy}%"}
            )
        return stats

    def _build_policies(self, owner_name: str) -> List[PolicyUpdate]:
        bullets = self._extract_plan_bullets("## 7. Kebijakan Akses & Peran")
        if self._plan_path.exists():
            updated_at = datetime.fromtimestamp(self._plan_path.stat().st_mtime).strftime("%d %b %Y")
        else:
            updated_at = datetime.now().strftime("%d %b %Y")
        policies: List[PolicyUpdate] = []
        for index, bullet in enumerate(bullets[:3], start=1):
            title = bullet.split("|")[0].strip().strip("-").strip()
            title = title.strip("* ")
            tags = [tag.strip().lower() for tag in title.split()[:2]]
            policies.append(
                PolicyUpdate(
                    title=title or f"Kebijakan #{index}",
                    version=f"v1.{index}",
                    updated_at=updated_at,
                    owner=owner_name,
                    tags=tags,
                )
            )
        return policies

    def _build_templates(self) -> List[dict]:
        return [
            {
                "name": "Template follow-up transaksi",
                "usage": "Moderator",
                "updated_at": "Minggu ini",
            },
            {
                "name": "Template klarifikasi kurasi",
                "usage": "Kurator",
                "updated_at": "3 hari lalu",
            },
            {
                "name": "Template eskalasi legal",
                "usage": "Admin",
                "updated_at": "1 minggu lalu",
            },
        ]

    def _build_help_resources(self) -> List[HelpResource]:
        bullets = self._extract_plan_bullets("## 5. Alur Pengguna Kunci")
        defaults = [
            (
                "Panduan audit quality lead",
                "Quality Lead",
                "Playbook",
                "April 2024",
            ),
            (
                "Checklist onboarding moderator",
                "Moderator",
                "Spreadsheet",
                "Maret 2024",
            ),
            (
                "Video training kurator",
                "Kurator",
                "Video",
                "Februari 2024",
            ),
        ]

        resources: List[HelpResource] = []
        for bullet, default in zip(bullets, defaults):
            resources.append(
                HelpResource(
                    title=bullet,
                    category=default[1],
                    format=default[2],
                    updated_at=default[3],
                )
            )

        if not resources:
            resources = [
                HelpResource(
                    title=title,
                    category=category,
                    format=file_format,
                    updated_at=updated,
                )
                for title, category, file_format, updated in defaults
            ]

        return resources

    def _build_contacts(self, team_members: Sequence[TeamMemberSummary]) -> List[ContactPoint]:
        contacts = []
        for index, member in enumerate(team_members[:3]):
            contacts.append(
                ContactPoint(
                    name=member.name,
                    role=member.role,
                    channel=f"Slack #{member.name.split()[0].lower()}-ops",
                    availability="09.00 - 18.00",
                )
            )
        return contacts

    # ------------------------------------------------------------------
    # Iterators & utilities
    # ------------------------------------------------------------------
    def _iter_highlights(self) -> Iterable[BrandHighlight]:
        for brand in self._brand_source.list_brands():
            for highlight in brand.highlights:
                yield highlight

    def _iter_story_points(self) -> Iterable[tuple[Brand, str]]:
        for brand in self._brand_source.list_brands():
            for story in brand.story_points:
                yield brand, story

    def _iter_products(self) -> Iterable[tuple[Brand, BrandProduct]]:
        for brand in self._brand_source.list_brands():
            for product in brand.products:
                yield brand, product

    def _extract_plan_bullets(self, marker: str, limit: int = 3) -> List[str]:
        if not self._plan_path.exists():
            return []

        text = self._plan_path.read_text(encoding="utf-8")
        try:
            section = text.split(marker, maxsplit=1)[1]
        except IndexError:
            return []

        lines: List[str] = []
        for raw_line in section.splitlines()[1:]:
            if raw_line.startswith("## ") and marker.startswith("## "):
                break
            if raw_line.startswith("### ") and marker.startswith("### "):
                break
            stripped = raw_line.strip()
            if stripped.startswith("- "):
                lines.append(stripped[2:].strip())
            if len(lines) >= limit:
                break
        return lines[:limit]

    @staticmethod
    def _format_currency(amount: float) -> str:
        return f"Rp {int(amount):,}".replace(",", ".")

    @staticmethod
    def _top_payment_method(records: Sequence[SalesRecord]) -> str:
        if not records:
            return "-"
        method = Counter(record.payment_method for record in records).most_common(1)[0][0]
        return method.replace("_", " ").title()

    @staticmethod
    def _classify_priority(total_amount: float) -> str:
        if total_amount >= 5_000_000:
            return "Merah"
        if total_amount >= 3_500_000:
            return "Kuning"
        return "Hijau"

    @staticmethod
    def _map_payment_to_category(payment_method: str) -> str:
        mapping = {
            "transfer": "Transaksi",
            "virtual_account": "Transaksi",
            "ewallet": "Pembeli",
            "cash_on_delivery": "Pembeli",
        }
        return mapping.get(payment_method, "Lainnya")


__all__ = ["ModerationDashboardRepository"]

