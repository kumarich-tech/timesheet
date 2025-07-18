from django.urls import path
from .views import (
    timesheet_view,
    export_timesheet_xlsx,
    import_timesheet_view,
    services_view,
    export_services_xlsx,
    export_salary_report_xlsx,
    report_view,
    export_salary_full_xlsx,
    export_salary_advance_xlsx,
)

urlpatterns = [
    path("timesheet/", timesheet_view, name="timesheet"),
    path("timesheet/import/", import_timesheet_view, name="import_timesheet"),
    path("timesheet/export/", export_timesheet_xlsx, name="export_timesheet"),
    path("services/", services_view, name="services"),
    path("services/export/", export_services_xlsx, name="export_services"),
    path("report/export/", export_salary_report_xlsx, name="export_salary_report"),
    path("report/", report_view, name="report"),
    path("export-advance/", export_salary_advance_xlsx, name="export_salary_advance"),
    path("export-salary/", export_salary_full_xlsx, name="export_salary_full"),
]
