from datetime import date
from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings

from utils.excel_export import build_timesheet_workbook


class Command(BaseCommand):
    help = "Send timesheet report via email"

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            help="Target month in YYYY-MM format. Defaults to current month",
        )

    def handle(self, *args, **options):
        month = options.get("month")
        if month:
            year, month_num = map(int, month.split("-"))
            first_day = date(year, month_num, 1)
        else:
            today = date.today()
            first_day = date(today.year, today.month, 1)

        wb = build_timesheet_workbook(first_day)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        subject = f"Табель за {first_day.strftime('%B %Y')}"
        email = EmailMessage(
            subject=subject,
            body="Автоматическая отправка табеля.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.REPORT_RECIPIENTS,
        )
        filename = f"tabel_{first_day.year}_{first_day.month:02d}.xlsx"
        email.attach(
            filename,
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        email.send()
        self.stdout.write(self.style.SUCCESS("Timesheet sent"))
