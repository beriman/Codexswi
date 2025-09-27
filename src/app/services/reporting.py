"""Services for generating sales reports and export files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from io import BytesIO, StringIO
from typing import Iterable, List
from zipfile import ZIP_DEFLATED, ZipFile

import csv
from xml.sax.saxutils import escape


@dataclass
class SalesRecord:
    """Represents a single sales record entry."""

    order_id: str
    order_date: date
    customer_name: str
    total_items: int
    total_amount: float
    payment_method: str
    status: str


class ExportFormat(str, Enum):
    """Supported export formats for sales reports."""

    CSV = "csv"
    XLSX = "xlsx"


class SalesReportService:
    """Service responsible for retrieving and exporting sales reports."""

    def __init__(self) -> None:
        self._seed_data = self._load_seed_data()

    def _load_seed_data(self) -> List[SalesRecord]:
        """Load a small in-memory dataset representing aggregated sales."""

        raw_data = [
            ("INV-2024-0401-01", "2024-04-01", "Anjani Parfums", 18, 6250000.0, "transfer", "settled"),
            ("INV-2024-0401-02", "2024-04-01", "Mahesa Retail", 9, 2485000.0, "virtual_account", "settled"),
            ("INV-2024-0402-01", "2024-04-02", "Studio Senja", 12, 3840000.0, "ewallet", "settled"),
            ("INV-2024-0403-01", "2024-04-03", "Rara Widyanti", 7, 1890000.0, "transfer", "pending"),
            ("INV-2024-0404-01", "2024-04-04", "Atar Nusantara", 14, 5125000.0, "transfer", "settled"),
            ("INV-2024-0405-01", "2024-04-05", "Sukma Fragrances", 6, 1575000.0, "cash_on_delivery", "settled"),
            ("INV-2024-0406-01", "2024-04-06", "Aura Lestari", 11, 3350000.0, "transfer", "settled"),
        ]

        return [
            SalesRecord(
                order_id=order_id,
                order_date=datetime.strptime(order_date, "%Y-%m-%d").date(),
                customer_name=customer_name,
                total_items=total_items,
                total_amount=total_amount,
                payment_method=payment_method,
                status=status,
            )
            for order_id, order_date, customer_name, total_items, total_amount, payment_method, status in raw_data
        ]

    def get_sales_report(self, start_date: date, end_date: date) -> List[SalesRecord]:
        """Return the sales records that fall within the selected date range."""

        return [
            record
            for record in self._seed_data
            if start_date <= record.order_date <= end_date
        ]

    def to_csv(self, records: Iterable[SalesRecord]) -> bytes:
        """Generate CSV bytes from a list of sales records."""

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Nomor Order",
                "Tanggal Order",
                "Nama Pelanggan",
                "Jumlah Item",
                "Total (Rp)",
                "Metode Pembayaran",
                "Status",
            ]
        )

        for record in records:
            writer.writerow(
                [
                    record.order_id,
                    record.order_date.isoformat(),
                    record.customer_name,
                    record.total_items,
                    f"{record.total_amount:.2f}",
                    record.payment_method,
                    record.status,
                ]
            )

        return buffer.getvalue().encode("utf-8")

    def to_xlsx(self, records: Iterable[SalesRecord]) -> bytes:
        """Generate XLSX bytes from a list of sales records without external deps."""

        header = [
            "Nomor Order",
            "Tanggal Order",
            "Nama Pelanggan",
            "Jumlah Item",
            "Total (Rp)",
            "Metode Pembayaran",
            "Status",
        ]

        rows = [header]
        for record in records:
            rows.append(
                [
                    record.order_id,
                    record.order_date.isoformat(),
                    record.customer_name,
                    str(record.total_items),
                    f"{record.total_amount:.2f}",
                    record.payment_method,
                    record.status,
                ]
            )

        sheet_rows = []
        for row_index, values in enumerate(rows, start=1):
            cells = []
            for col_index, value in enumerate(values, start=1):
                column_letter = self._column_letter(col_index)
                cell_reference = f"{column_letter}{row_index}"
                escaped = escape(str(value))
                cells.append(
                    f"<c r=\"{cell_reference}\" t=\"inlineStr\"><is><t>{escaped}</t></is></c>"
                )
            sheet_rows.append(f"<row r=\"{row_index}\">{''.join(cells)}</row>")

        sheet_data = "".join(sheet_rows)
        sheet_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            f"<sheetData>{sheet_data}</sheetData>"
            "</worksheet>"
        )

        workbook_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheets><sheet name=\"Sales Report\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
            "</workbook>"
        )

        workbook_rels = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
            "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>"
            "</Relationships>"
        )

        styles_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            "<fonts count=\"1\"><font><sz val=\"11\"/><name val=\"Calibri\"/></font></fonts>"
            "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
            "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>"
            "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
            "<cellXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/></cellXfs>"
            "</styleSheet>"
        )

        rels_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
            "</Relationships>"
        )

        content_types_xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
            "</Types>"
        )

        stream = BytesIO()
        with ZipFile(stream, mode="w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types_xml)
            archive.writestr("_rels/.rels", rels_xml)
            archive.writestr("xl/workbook.xml", workbook_xml)
            archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
            archive.writestr("xl/styles.xml", styles_xml)

        return stream.getvalue()

    def _column_letter(self, index: int) -> str:
        result = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result


sales_report_service = SalesReportService()
"""Default singleton instance used by the application."""

