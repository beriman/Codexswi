"""Routes for exporting sales reports."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.reporting import ExportFormat, SalesRecord, SalesReportService, sales_report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_sales_report_service() -> SalesReportService:
    """Dependency returning the shared sales report service instance."""

    return sales_report_service


def _validate_dates(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")


def _export_records(
    records: Iterable[SalesRecord],
    export_format: ExportFormat,
    service: SalesReportService,
) -> tuple[bytes, str, str]:
    if export_format is ExportFormat.CSV:
        content = service.to_csv(records)
        media_type = "text/csv"
        extension = "csv"
    elif export_format is ExportFormat.XLSX:
        content = service.to_xlsx(records)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        extension = "xlsx"
    else:  # pragma: no cover - Enum guards ensure this won't run but kept for safety.
        raise HTTPException(status_code=400, detail="Unsupported export format")

    return content, media_type, extension


@router.get("/sales/export")
def export_sales_report(
    start_date: date = Query(..., description="Tanggal awal rentang laporan"),
    end_date: date = Query(..., description="Tanggal akhir rentang laporan"),
    export_format: ExportFormat = Query(ExportFormat.CSV, alias="format", description="Format file yang diunduh"),
    service: SalesReportService = Depends(get_sales_report_service),
) -> StreamingResponse:
    """Return a downloadable sales report in the requested format."""

    _validate_dates(start_date, end_date)

    records = service.get_sales_report(start_date=start_date, end_date=end_date)
    if not records:
        raise HTTPException(status_code=404, detail="No sales data available for the selected range")

    content, media_type, extension = _export_records(records, export_format, service)

    filename = f"sales-report-{start_date.isoformat()}-to-{end_date.isoformat()}.{extension}"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(iter([content]), media_type=media_type, headers=headers)

