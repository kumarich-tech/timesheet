from django.db import models

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Отдел")

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=100, verbose_name="Должность")

    def __str__(self):
        return self.name


class Employee(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    day_shift_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ставка дневной смены")
    night_shift_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ставка ночной смены")
    is_fixed_salary = models.BooleanField(default=False, verbose_name="Окладная оплата")
    fixed_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Оклад")
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Премия")

    def __str__(self):
        return self.full_name

    class Meta:
        permissions = [
            ("import_employees", "Can import employees from Excel"),
        ]


class ShiftType(models.TextChoices):
    DAY = "day", "День"
    NIGHT = "night", "Ночь"
    WEEKEND = "weekend", "Выходной"
    VACATION = "vacation", "Отпуск"
    SICK = "sick", "Больничный"
    PARTIAL = "partial", "Неполная"


class WorkSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=ShiftType.choices)

    class Meta:
        unique_together = ('employee', 'date')
        permissions = [
            ("export_timesheet", "Can export timesheet"),
            ("export_salary", "Can export salary reports"),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.get_shift_display()})"


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name="Услуга")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена за единицу")
    for_salary_based = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class EmployeeServiceRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    month = models.DateField(help_text="Указываем 1-е число месяца (например, 2024-06-01)")
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('employee', 'service', 'month')
        permissions = [
            ("export_services", "Can export services"),
        ]

    def __str__(self):
        return f"{self.employee} - {self.service} ({self.month})"


class Settings(models.Model):
    partial_shift_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.5, verbose_name="Коэффициент неполной смены"
    )
    vacation_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, verbose_name="Коэффициент отпуска"
    )
    sick_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, verbose_name="Коэффициент больничного"
    )

    class Meta:
        verbose_name = "Настройки расчёта"
        verbose_name_plural = "Настройки расчёта"

    def __str__(self):
        return "Глобальные настройки расчёта"

    @classmethod
    def get(cls):
        return cls.objects.first() or cls.objects.create()


class ScheduleTemplate(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название шаблона")
    sequence = models.JSONField(verbose_name="Последовательность смен")

    class Meta:
        verbose_name = "Шаблон графика"
        verbose_name_plural = "Шаблоны графиков"

    def __str__(self):
        return self.name
