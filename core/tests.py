from datetime import date
from django.test import TestCase
from django.urls import reverse

from .models import (
    Department,
    Position,
    Employee,
    WorkSchedule,
    Service,
    EmployeeServiceRecord,
)


class TimesheetViewTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Dep")
        self.position = Position.objects.create(name="Worker")
        self.employee = Employee.objects.create(
            full_name="John Doe",
            department=self.department,
            position=self.position,
        )

    def test_get_timesheet(self):
        url = reverse("timesheet") + "?month=2024-01"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.employee, list(response.context["employees"]))

    def test_post_timesheet_creates_schedule(self):
        month = date.today().strftime("%Y-%m")
        url = reverse("timesheet") + f"?month={month}"
        resp = self.client.post(url, {f"shift_{self.employee.id}_1": "day"})
        self.assertEqual(resp.status_code, 302)
        month_first = date.today().replace(day=1)
        self.assertTrue(
            WorkSchedule.objects.filter(
                employee=self.employee, date=month_first, shift="day"
            ).exists()
        )


class ServicesViewTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Dep")
        self.position = Position.objects.create(name="Worker")
        self.employee = Employee.objects.create(
            full_name="John Doe",
            department=self.department,
            position=self.position,
            is_fixed_salary=False,
        )
        self.service = Service.objects.create(
            name="Test Service", price=100, for_salary_based=False
        )

    def test_get_services(self):
        url = reverse("services") + "?month=2024-01"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.service, list(response.context["services"]))

    def test_post_services_creates_record(self):
        month = date.today().strftime("%Y-%m")
        url = reverse("services") + f"?month={month}"
        resp = self.client.post(
            url, {f"s_{self.employee.id}_{self.service.id}": "2"}
        )
        self.assertEqual(resp.status_code, 302)
        month_first = date.today().replace(day=1)
        record = EmployeeServiceRecord.objects.get(
            employee=self.employee, service=self.service, month=month_first
        )
        self.assertEqual(record.quantity, 2)
