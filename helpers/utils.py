from datetime import date, timedelta
from calendar import monthrange

from core.models import Employee, WorkSchedule, EmployeeServiceRecord


def parse_month(request) -> date:
    month_str = request.GET.get("month")
    if month_str:
        try:
            year, month = map(int, month_str.split("-"))
            return date(year, month, 1)
        except Exception:
            pass
    today = date.today()
    return date(today.year, today.month, 1)


def get_employees_queryset():
    return Employee.objects.select_related("department", "position").all()


def get_working_days(year: int, month: int) -> int:
    total_days = monthrange(year, month)[1]
    return sum(1 for d in range(1, total_days + 1) if date(year, month, d).weekday() < 5)


def get_schedule_maps(first_day: date):
    """Return schedule_map and last_shift_map for given month."""
    year, month = first_day.year, first_day.month
    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)
    schedule_map: dict[int, dict[int, str]] = {}
    for s in schedule:
        schedule_map.setdefault(s.employee_id, {})[s.date.day] = s.shift

    prev_month_last_date = first_day.replace(day=1) - timedelta(days=1)
    prev_schedules = WorkSchedule.objects.filter(date=prev_month_last_date)
    last_shift_map = {s.employee_id: s.shift for s in prev_schedules}
    return schedule_map, last_shift_map


def build_service_data(records):
    data: dict[int, dict[int, int]] = {}
    for r in records:
        data.setdefault(r.employee.id, {})[r.service.id] = r.quantity
    return data

