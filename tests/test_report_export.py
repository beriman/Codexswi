import asyncio
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from xml.etree import ElementTree as ET

from app.api.routes.reports import export_sales_report
from app.services.reporting import ExportFormat, sales_report_service


def test_sales_report_service_filters_by_date():
    records = sales_report_service.get_sales_report(
        start_date=date(2024, 4, 2),
        end_date=date(2024, 4, 3),
    )

    assert len(records) == 2
    assert {record.order_id for record in records} == {"INV-2024-0402-01", "INV-2024-0403-01"}


def test_export_sales_report_csv():
    async def _run() -> None:
        response = export_sales_report(
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 4),
            export_format=ExportFormat.CSV,
            service=sales_report_service,
        )

        body = b"".join([chunk async for chunk in response.body_iterator])

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "attachment" in response.headers["content-disposition"]
        assert b"INV-2024-0401-01" in body
        assert body.startswith(b"Nomor Order")

    asyncio.run(_run())


def test_export_sales_report_xlsx():
    async def _run() -> None:
        response = export_sales_report(
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 4),
            export_format=ExportFormat.XLSX,
            service=sales_report_service,
        )

        body = b"".join([chunk async for chunk in response.body_iterator])

        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with ZipFile(BytesIO(body)) as archive:
            sheet_xml = archive.read("xl/worksheets/sheet1.xml")

        root = ET.fromstring(sheet_xml)
        namespace = {"ss": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = root.findall("ss:sheetData/ss:row", namespace)

        assert len(rows) >= 2
        header_cells = rows[0].findall("ss:c/ss:is/ss:t", namespace)
        first_row_cells = rows[1].findall("ss:c/ss:is/ss:t", namespace)

        assert header_cells[0].text == "Nomor Order"
        assert first_row_cells[0].text == "INV-2024-0401-01"

    asyncio.run(_run())
