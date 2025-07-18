from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import date, datetime, timedelta
from calendar import monthrange
from io import BytesIO
from django.db.models import Q
from decimal import Decimal

import openpyxl
from openpyxl.styles import Font

from .models import (
    Employee,
    WorkSchedule,
    ShiftType,
    Service,
    EmployeeServiceRecord,
    Department,
)


def parse_month(request):
    month_str = request.GET.get("month")
    if month_str:
        try:
            year, month = map(int, month_str.split("-"))
            return date(year, month, 1)
        except:
            pass
    today = date.today()
    return date(today.year, today.month, 1)


def timesheet_view(request):

    first_day = parse_month(request)
    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]
    today = date.today()

    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    days_info = []
    for d in range(1, days_in_month + 1):
        dt = date(year, month, d)
        days_info.append({
            'num': d,
            'weekday': day_names[dt.weekday()],
            'is_today': dt == today,
            'is_weekend': dt.weekday() >= 5,
        })

    department_id = request.GET.get("department")
    employees = Employee.objects.all()
    if department_id:
        employees = employees.filter(department_id=department_id)

    if request.method == "POST":
        for employee in employees:
            for day in range(1, days_in_month + 1):
                field_name = f"shift_{employee.id}_{day}"
                shift_value = request.POST.get(field_name)
                if shift_value:
                    date_obj = date(year, month, day)
                    WorkSchedule.objects.update_or_create(
                        employee=employee,
                        date=date_obj,
                        defaults={"shift": shift_value}
                    )
        redirect_url = f"{request.path}?month={first_day.strftime('%Y-%m')}"
        if department_id:
            redirect_url += f"&department={department_id}"
        return redirect(redirect_url)

    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)
    schedule_map = {}

    # Получаем смены на последний день предыдущего месяца
    prev_month_last_date = first_day.replace(day=1) - timedelta(days=1)
    prev_schedules = WorkSchedule.objects.filter(date=prev_month_last_date)
    last_shift_map = {s.employee_id: s.shift for s in prev_schedules}
    for s in schedule:
        schedule_map.setdefault(s.employee_id, {})[s.date.day] = s.shift

    salary_summary = {}
    for employee in employees:
        shifts = schedule_map.get(employee.id, {})
        day_count = sum(1 for shift in shifts.values() if shift == 'day')
        night_count = sum(1 for shift in shifts.values() if shift == 'night')

        if employee.is_fixed_salary:
            total_salary = float(employee.fixed_salary) + float(employee.bonus)
        else:
            total_salary = day_count * float(employee.day_shift_rate) + night_count * float(employee.night_shift_rate)

        salary_summary[employee.id] = {
            "day": day_count,
            "night": night_count,
            "total": total_salary,
        }

    departments = Department.objects.all()
    return render(request, "core/timesheet.html", {
        "employees": employees,
        "days": range(1, days_in_month + 1),
        "days_info": days_info,
        "month": first_day,
        "schedule": schedule_map,
        "salary": salary_summary,
        "shift_choices": [
    ("day", "Д"),
    ("night", "Н"),
    ("weekend", "В"),
    ("vacation", "О"),
    ("sick", "Б"),
],
        "departments": departments,
        "selected_department": department_id,
        "last_shifts": last_shift_map,
    })


def export_timesheet_xlsx(request):
    first_day = parse_month(request)
    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]

    employees = Employee.objects.all()
    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)

    schedule_map = {}

    # Получаем смены на последний день предыдущего месяца
    prev_month_last_date = first_day.replace(day=1) - timedelta(days=1)
    prev_schedules = WorkSchedule.objects.filter(date=prev_month_last_date)
    last_shift_map = {s.employee_id: s.shift for s in prev_schedules}
    for s in schedule:
        schedule_map.setdefault(s.employee_id, {})[s.date.day] = s.shift

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Табель_{year}_{month:02d}"

    headers = ["ФИО", "Отдел", "Должность"]
    headers += [str(d) for d in range(1, days_in_month + 1)]
    headers += ["Дневных", "Ночных", "Итого (₽)"]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for employee in employees:
        row = [
            employee.full_name,
            employee.department.name,
            employee.position.name,
        ]
        shifts = schedule_map.get(employee.id, {})
        day_count = 0
        night_count = 0

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

        total_salary = day_count * float(employee.day_shift_rate) + night_count * float(employee.night_shift_rate)
        row += [day_count, night_count, round(total_salary, 2)]

        ws.append(row)

    for col in ws.columns:
        max_len = max((len(str(cell.value)) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="tabel_{year}_{month:02d}.xlsx"'
    return response

def services_view(request):
    first_day = parse_month(request)
    year, month = first_day.year, first_day.month
    employees = Employee.objects.all()
    services = Service.objects.all()
    selected_department = request.GET.get("department")

    if selected_department:
        employees = employees.filter(department_id=selected_department)

    if request.method == "POST":
        for employee in employees:
            # Используем фильтр по типу сотрудника
            filtered_services = services.filter(for_salary_based=employee.is_fixed_salary)
            for service in filtered_services:
                field = f"s_{employee.id}_{service.id}"
                qty = request.POST.get(field)
                if qty:
                    qty = int(qty)
                    EmployeeServiceRecord.objects.update_or_create(
                        employee=employee,
                        service=service,
                        month=first_day,
                        defaults={"quantity": qty}
                    )
        return redirect(f"{request.path}?month={first_day.strftime('%Y-%m')}&department={selected_department or ''}")

    records = EmployeeServiceRecord.objects.filter(month=first_day)
    data = {}
    for rec in records:
        data[(rec.employee.id, rec.service.id)] = rec.quantity

    summary = {}
    for employee in employees:
        total = 0
        filtered_services = services.filter(for_salary_based=employee.is_fixed_salary)
        for service in filtered_services:
            qty = data.get((employee.id, service.id), 0)
            total += qty * float(service.price)
        summary[employee.id] = total

    departments = Department.objects.all()

    return render(request, "core/services.html", {
        "employees": employees,
        "services": services,
        "month": first_day,
        "data": data,
        "summary": summary,
        "departments": departments,
        "selected_department": selected_department,
    })
def export_services_xlsx(request):
    first_day = parse_month(request)
    year, month = first_day.year, first_day.month

    employees = Employee.objects.all()
    services = Service.objects.all()
    records = EmployeeServiceRecord.objects.filter(month=first_day)

    data = {}
    for r in records:
        data[(r.employee.id, r.service.id)] = r.quantity

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Услуги_{year}_{month:02d}"

    headers = ["ФИО", "Отдел", "Должность"] + [s.name for s in services] + ["Итого (₽)"]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for emp in employees:
        row = [emp.full_name, emp.department.name, emp.position.name]
        total = 0
        for s in services:
            qty = data.get((emp.id, s.id), 0)
            row.append(qty)
            total += qty * float(s.price)
        row.append(round(total, 2))
        ws.append(row)

    for col in ws.columns:
        max_len = max((len(str(cell.value)) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="uslugi_{year}_{month:02d}.xlsx"'
    return response


def export_salary_report_xlsx(request):
    first_day = parse_month(request)
    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]

    employees = Employee.objects.all()
    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)
    records = EmployeeServiceRecord.objects.filter(month=first_day)
    services = Service.objects.all()

    schedule_map = {}

    # Получаем смены на последний день предыдущего месяца
    prev_month_last_date = first_day.replace(day=1) - timedelta(days=1)
    prev_schedules = WorkSchedule.objects.filter(date=prev_month_last_date)
    last_shift_map = {s.employee_id: s.shift for s in prev_schedules}
    for s in schedule:
        schedule_map.setdefault(s.employee_id, {})[s.date.day] = s.shift

    service_data = {}
    for r in records:
        service_data.setdefault(r.employee.id, {})[r.service.id] = r.quantity

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Зарплата_{year}_{month:02d}"

    headers = [
        "ФИО", "Отдел", "Должность",
        "Дневных", "Ночных", "Сумма смен (₽)", "Сумма услуг (₽)", "Итого (₽)"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for emp in employees:
        shifts = schedule_map.get(emp.id, {})
        day_count = sum(1 for shift in shifts.values() if shift == "day")
        night_count = sum(1 for shift in shifts.values() if shift == "night")
        salary_shifts = day_count * float(emp.day_shift_rate) + night_count * float(emp.night_shift_rate)

        service_sum = 0
        for s in services:
            qty = service_data.get(emp.id, {}).get(s.id, 0)
            service_sum += qty * float(s.price)

        total = round(salary_shifts + service_sum, 2)

        ws.append([
            emp.full_name,
            emp.department.name,
            emp.position.name,
            day_count,
            night_count,
            round(salary_shifts, 2),
            round(service_sum, 2),
            total
        ])

    for col in ws.columns:
        max_len = max((len(str(cell.value)) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="zarplata_{year}_{month:02d}.xlsx"'
    return response


def report_view(request):
    first_day = parse_month(request)
    selected_department = request.GET.get("department")
    report_type = request.GET.get("type")  # "advance" или "final"

    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]
    employees = Employee.objects.all()
    if selected_department:
        employees = employees.filter(department_id=selected_department)

    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)
    schedule_map = {}

    # Получаем смены на последний день предыдущего месяца
    prev_month_last_date = first_day.replace(day=1) - timedelta(days=1)
    prev_schedules = WorkSchedule.objects.filter(date=prev_month_last_date)
    last_shift_map = {s.employee_id: s.shift for s in prev_schedules}
    for s in schedule:
        schedule_map.setdefault(s.employee_id, {})[s.date.day] = s.shift

    services = Service.objects.all()
    records = EmployeeServiceRecord.objects.filter(month=first_day)
    service_data = {}
    for r in records:
        service_data.setdefault(r.employee.id, {})[r.service.id] = r.quantity

    salary_summary = []
    mid_month = 15

    for emp in employees:
        shifts = schedule_map.get(emp.id, {})
        day_count = sum(1 for d, s in shifts.items() if s == "day")
        night_count = sum(1 for d, s in shifts.items() if s == "night")
        total_shift_salary = day_count * float(emp.day_shift_rate) + night_count * float(emp.night_shift_rate)

        service_sum = 0
        for s in services:
            qty = service_data.get(emp.id, {}).get(s.id, 0)
            service_sum += qty * float(s.price)

        if emp.is_fixed_salary:
            total_days = sum(1 for s in shifts.values() if s in ["day", "night"])
            worked_days_1_15 = sum(
                1 for d, s in shifts.items() if s in ["day", "night"] and d <= mid_month
            )
            salary_base = (
                (float(emp.fixed_salary) / total_days) * total_days if total_days else 0
            )
            total_salary = salary_base + float(emp.bonus) + service_sum

            if report_type == "advance":
                advance = (
                    (float(emp.fixed_salary) / total_days) * worked_days_1_15 if total_days else 0
                )
                salary_summary.append({
                    "employee": emp,
                    "day": worked_days_1_15,
                    "night": 0,
                    "shifts_sum": round(advance),
                    "services_sum": 0,
                    "total": round(advance),
                })
                continue
        else:
            total_salary = total_shift_salary + service_sum

        salary_summary.append({
            "employee": emp,
            "day": day_count,
            "night": night_count,
            "shifts_sum": round(total_shift_salary),
            "services_sum": round(service_sum),
            "total": round(total_salary),
        })

    return render(request, "core/report.html", {
        "month": first_day,
        "departments": Department.objects.all(),
        "selected_department": selected_department,
        "report_type": report_type,
        "salary_summary": salary_summary,
    })
def export_salary_full_xlsx(request):
    return generate_salary_report(request, full_month=True)

def export_salary_advance_xlsx(request):
    return generate_salary_report(request, full_month=False)

def generate_salary_report(request, full_month=True):
    from calendar import monthrange
    from openpyxl import Workbook
    from openpyxl.styles import Font

    first_day = parse_month(request)
    year, month = first_day.year, first_day.month
    days_in_month = monthrange(year, month)[1]

    employees = Employee.objects.all()
    selected_department = request.GET.get("department")
    if selected_department:
        employees = employees.filter(department_id=selected_department)

    schedule = WorkSchedule.objects.filter(date__year=year, date__month=month)
    records = EmployeeServiceRecord.objects.filter(month=first_day)
    services = Service.objects.all()

    service_data = {}
    for r in records:
        service_data.setdefault(r.employee.id, {})[r.service.id] = r.quantity

    wb = Workbook()
    ws = wb.active
    ws.title = "Аванс" if not full_month else "Зарплата"

    headers = ["ФИО", "Отдел", "Должность", "Дневных", "Ночных", "Сумма смен (₽)", "Сумма услуг (₽)", "Премия", "Итого (₽)"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for emp in employees:
        shifts = {s.date.day: s.shift for s in schedule if s.employee_id == emp.id}

        if full_month:
            period_days = range(1, days_in_month + 1)
        else:
            period_days = range(1, 16)  # с 1 по 15

        day_count = sum(1 for d in period_days if shifts.get(d) == "day")
        night_count = sum(1 for d in period_days if shifts.get(d) == "night")

        if emp.is_fixed_salary:
            total_days = sum(1 for d in range(1, days_in_month + 1) if shifts.get(d) in ["day", "night"])
            worked_days = sum(1 for d in period_days if shifts.get(d) in ["day", "night"])
            base = (emp.fixed_salary or 0) / total_days if total_days else 0
            salary_shift_sum = round(base * worked_days, 2)
        else:
            salary_shift_sum = round(day_count * float(emp.day_shift_rate) + night_count * float(emp.night_shift_rate), 2)

        service_sum = 0
        for s in services:
            qty = service_data.get(emp.id, {}).get(s.id, 0)
            service_sum += qty * float(s.price)

        bonus = float(emp.bonus or 0) if full_month else 0
        total = Decimal(salary_shift_sum) + (Decimal(service_sum) if full_month else Decimal(0)) + Decimal(bonus)

        ws.append([
            emp.full_name,
            emp.department.name,
            emp.position.name,
            day_count,
            night_count,
            salary_shift_sum,
            round(service_sum if full_month else 0, 2),
            round(bonus, 2),
            round(total, 2)
        ])

    # автоширина
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value)) for c in col) + 2

    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{'avans' if not full_month else 'zarplata'}_{year}_{month:02d}.xlsx"
    response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

