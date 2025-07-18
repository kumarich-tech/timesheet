from io import BytesIO
from django.http import HttpResponse
from openpyxl.styles import Font


def autofit_columns(ws):
    """Auto adjust column width based on cell contents."""
    for col in ws.columns:
        max_len = max((len(str(cell.value)) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2


def workbook_to_response(wb, filename: str) -> HttpResponse:
    """Save workbook to HTTP response with given filename."""
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename=\"{filename}\""
    return response

