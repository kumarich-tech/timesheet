from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    Department,
    Position,
    Employee,
    WorkSchedule,
    Service,
    EmployeeServiceRecord,
    Settings,
    ScheduleTemplate,
)
import openpyxl

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price")

@admin.register(WorkSchedule)
class WorkScheduleAdmin(SimpleHistoryAdmin):
    list_display = ("employee", "date", "shift")
    list_filter = ("shift", "date")

@admin.register(EmployeeServiceRecord)
class EmployeeServiceRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "service", "month", "quantity")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "position", "is_fixed_salary", "fixed_salary", "bonus")
    list_filter = ("department", "position", "is_fixed_salary")
    search_fields = ("full_name",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-employees/", self.admin_site.admin_view(self.import_employees), name="import_employees"),
        ]
        return custom_urls + urls

    def import_employees(self, request):
        if request.method == "POST" and request.FILES.get("xlsx_file"):
            wb = openpyxl.load_workbook(request.FILES["xlsx_file"])
            ws = wb.active
            count = 0
            for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
                full_name = row[0].value
                dept_name = row[1].value
                pos_name = row[2].value
                day_rate = row[3].value
                night_rate = row[4].value
                if not all([full_name, dept_name, pos_name, day_rate, night_rate]):
                    continue
                dept, _ = Department.objects.get_or_create(name=dept_name)
                pos, _ = Position.objects.get_or_create(name=pos_name)
                Employee.objects.update_or_create(
                    full_name=full_name,
                    defaults={
                        "department": dept,
                        "position": pos,
                        "day_shift_rate": day_rate,
                        "night_shift_rate": night_rate,
                    }
                )
                count += 1
            self.message_user(request, f"Импортировано {count} сотрудников.")
            return redirect("..")
        return render(request, "admin/import_employees_admin.html")

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ("partial_shift_multiplier", "vacation_multiplier", "sick_multiplier")


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ("name",)
