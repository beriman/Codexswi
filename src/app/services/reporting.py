"""Services for generating sales reports and export files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from io import BytesIO, StringIO
from typing import Iterable, List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

import csv
import logging
from xml.sax.saxutils import escape

try:
    from supabase import Client
except ImportError:
    Client = None  # type: ignore

logger = logging.getLogger(__name__)


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

    def __init__(self, db: Optional[Client] = None) -> None:
        self.db = db
        logger.info(f"SalesReportService initialized with {'Supabase' if db else 'no database'}")

    def get_sales_report(
        self, 
        start_date: date, 
        end_date: date,
        customer_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[SalesRecord]:
        """Return the sales records that fall within the selected date range.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            customer_id: Optional customer ID filter
            brand_id: Brand name to filter by (NOTE: parameter named brand_id for API compatibility,
                     but currently matches against order_items.brand_name due to schema limitation.
                     Future enhancement: add proper brand_id join via products table)
            status_filter: Optional order status filter
        
        Note:
            The order_items table only stores brand_name, not brand_id. To filter by brand,
            pass the brand NAME as the brand_id parameter value.
        """
        
        if not self.db:
            logger.warning("No database connection - returning fallback sales report")
            return self._get_fallback_report(start_date, end_date, customer_id, brand_id, status_filter)
        
        try:
            # Query orders with items and brand info
            query = self.db.table('orders').select(
                '''
                id,
                order_number,
                customer_id,
                status,
                payment_status,
                total_amount,
                created_at,
                order_items(quantity, brand_name, product_id),
                auth_accounts!orders_customer_id_fkey(full_name)
                '''
            )
            
            # Apply date filter
            query = query.gte('created_at', start_date.isoformat())
            query = query.lte('created_at', f"{end_date.isoformat()}T23:59:59")
            
            # Apply optional filters
            if customer_id:
                query = query.eq('customer_id', customer_id)
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            result = query.execute()
            
            if not result.data:
                logger.info(f"No orders found for date range {start_date} to {end_date}")
                return []
            
            # Map to SalesRecord
            records = []
            for order in result.data:
                # Get customer name
                customer_name = "Unknown Customer"
                if order.get('auth_accounts'):
                    customer_name = order['auth_accounts'].get('full_name', 'Unknown Customer')
                
                # Calculate total items
                total_items = sum(item.get('quantity', 0) for item in order.get('order_items', []))
                
                # Check brand filter if specified (brand_id can be brand name or ID)
                if brand_id:
                    order_items = order.get('order_items', [])
                    # Match against brand_name in order_items (this is the actual field available)
                    has_brand = any(item.get('brand_name') == brand_id for item in order_items)
                    if not has_brand:
                        continue
                
                # Parse order date
                order_date_str = order.get('created_at', '')
                try:
                    order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError):
                    order_date = datetime.now().date()
                
                # Map payment status to method (simplified for now)
                payment_method = self._map_payment_method(order.get('payment_status', 'unknown'))
                
                record = SalesRecord(
                    order_id=order.get('order_number', order.get('id', '')),
                    order_date=order_date,
                    customer_name=customer_name,
                    total_items=total_items,
                    total_amount=float(order.get('total_amount', 0)),
                    payment_method=payment_method,
                    status=order.get('status', 'unknown')
                )
                records.append(record)
            
            logger.info(f"Retrieved {len(records)} sales records for date range {start_date} to {end_date}")
            return records
            
        except Exception as e:
            logger.error(f"Error fetching sales report: {str(e)}", exc_info=True)
            return []
    
    def _get_fallback_report(
        self, 
        start_date: date, 
        end_date: date, 
        customer_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[SalesRecord]:
        """Return fallback seed data for testing/development without database."""
        # Seed data format: (order_id, date, customer_id, customer_name, brand_name, items, amount, method, status)
        raw_data = [
            ("INV-2024-0401-01", "2024-04-01", "cust_001", "Anjani Parfums", "Langit Senja", 18, 6250000.0, "transfer", "settled"),
            ("INV-2024-0401-02", "2024-04-01", "cust_002", "Mahesa Retail", "Studio Senja", 9, 2485000.0, "virtual_account", "settled"),
            ("INV-2024-0402-01", "2024-04-02", "cust_003", "Studio Senja", "Atar Nusantara", 12, 3840000.0, "ewallet", "settled"),
            ("INV-2024-0403-01", "2024-04-03", "cust_001", "Rara Widyanti", "Langit Senja", 7, 1890000.0, "transfer", "pending"),
            ("INV-2024-0404-01", "2024-04-04", "cust_004", "Atar Nusantara", "Atar Nusantara", 14, 5125000.0, "transfer", "settled"),
            ("INV-2024-0405-01", "2024-04-05", "cust_005", "Sukma Fragrances", "Studio Senja", 6, 1575000.0, "cash_on_delivery", "settled"),
            ("INV-2024-0406-01", "2024-04-06", "cust_001", "Aura Lestari", "Langit Senja", 11, 3350000.0, "transfer", "settled"),
        ]
        
        records = []
        for order_id, order_date, cust_id, customer_name, brand, total_items, total_amount, payment_method, status in raw_data:
            order_date_obj = datetime.strptime(order_date, "%Y-%m-%d").date()
            
            # Apply all filters
            if start_date <= order_date_obj <= end_date:
                if customer_id and cust_id != customer_id:
                    continue
                # brand_id can be brand name or ID - match against brand name in seed data
                if brand_id and brand != brand_id:
                    continue
                if status_filter and status != status_filter:
                    continue
                    
                records.append(SalesRecord(
                    order_id=order_id,
                    order_date=order_date_obj,
                    customer_name=customer_name,
                    total_items=total_items,
                    total_amount=total_amount,
                    payment_method=payment_method,
                    status=status,
                ))
        
        return records
    
    def _map_payment_method(self, payment_status: str) -> str:
        """Map payment status to payment method for display."""
        # This is a simplified mapping - in production you'd have a payment_method field
        if payment_status == 'paid':
            return 'transfer'
        elif payment_status == 'pending':
            return 'pending'
        else:
            return 'unknown'

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

