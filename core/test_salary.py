from datetime import date
from django.urls import reverse
from django.test import TestCase

from .models import Department, Position, Employee, WorkSchedule

class SalaryReportTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Dep")
        self.position = Position.objects.create(name="Worker")
        self.employee = Employee.objects.create(
            full_name="John Doe",
            department=self.department,
            position=self.position,
            is_fixed_salary=True,
            fixed_salary=20000,
        )
        month = date(2024, 1, 1)
        for day in range(1, 11):
            WorkSchedule.objects.create(
                employee=self.employee,
                date=month.replace(day=day),
                shift="day",
            )

    def test_final_salary_deducts_advance(self):
        month_str = "2024-01"
        advance_url = reverse("report") + f"?month={month_str}&type=advance"
        resp_adv = self.client.get(advance_url)
        advance_total = resp_adv.context["salary_summary"][0]["total"]

        final_url = reverse("report") + f"?month={month_str}&type=final"
        resp_final = self.client.get(final_url)
        final_total = resp_final.context["salary_summary"][0]["total"]

        self.assertEqual(advance_total, 10000)
        self.assertEqual(final_total, 10000)
