from io import BytesIO
from calendar import monthrange
from datetime import date

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from helpers.utils import get_employees_queryset, get_schedule_maps
from services.payroll import calculate_shift_salary


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


def build_timesheet_workbook(first_day: date) -> Workbook:
    """Create workbook with timesheet data for given month."""
    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]

    employees = get_employees_queryset().order_by("department__name", "full_name")
    schedule_map, _ = get_schedule_maps(first_day)

    wb = Workbook()
    ws = wb.active
    ws.title = f"Табель_{year}_{month:02d}"

    headers = ["ФИО", "Отдел", "Должность"]
    headers += [str(d) for d in range(1, days_in_month + 1)]
    headers += ["Дневных", "Ночных", "Итого (₽)"]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for employee in employees:
        row = [employee.full_name, employee.department.name, employee.position.name]
        shifts = schedule_map.get(employee.id, {})
        day_count = night_count = 0
        for d in range(1, days_in_month + 1):
            shift = shifts.get(d, "")
            if shift == "day":
                row.append("Д")
                day_count += 1
            elif shift == "night":
                row.append("Н")
                night_count += 1
            elif shift == "vacation":
                row.append("О")
            elif shift == "sick":
                row.append("Б")
            elif shift == "weekend":
                row.append("В")
            else:
                row.append("")

        total_salary = calculate_shift_salary(employee, day_count, night_count)
        row += [day_count, night_count, round(float(total_salary), 2)]
        ws.append(row)

    autofit_columns(ws)
    return wb
