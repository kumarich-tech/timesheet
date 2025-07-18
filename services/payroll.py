from decimal import Decimal
from typing import Iterable, Dict

from core.models import Service, WorkSchedule


SHIFT_DAY = 'day'
SHIFT_NIGHT = 'night'
WORK_SHIFTS = {SHIFT_DAY, SHIFT_NIGHT}


def count_shifts(shifts: Dict[int, str], period_days: Iterable[int] | None = None) -> tuple[int, int]:
    """Return number of day and night shifts in the given period."""
    day_count = night_count = 0
    for day, shift in shifts.items():
        if period_days is not None and day not in period_days:
            continue
        if shift == SHIFT_DAY:
            day_count += 1
        elif shift == SHIFT_NIGHT:
            night_count += 1
    return day_count, night_count


def calculate_shift_salary(employee, day_count: int, night_count: int, *, worked_days: int | None = None, working_days_total: int | None = None) -> Decimal:
    """Calculate salary for shifts for the given employee."""
    if employee.is_fixed_salary:
        if worked_days is not None and working_days_total:
            base = (Decimal(employee.fixed_salary) / working_days_total) * worked_days
        else:
            base = Decimal(employee.fixed_salary)
        return base + Decimal(employee.bonus or 0)
    return (
        Decimal(day_count) * Decimal(employee.day_shift_rate)
        + Decimal(night_count) * Decimal(employee.night_shift_rate)
    )


def calculate_service_sum(services: Iterable[Service], quantities: Dict[int, int]) -> Decimal:
    """Calculate total cost of provided services."""
    total = Decimal(0)
    for service in services:
        qty = quantities.get(service.id, 0)
        total += Decimal(qty) * Decimal(service.price)
    return total

