# Generated by Django 5.2.3 on 2025-07-02 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_service_for_salary_based'),
    ]

    operations = [
        migrations.AddField(
            model_name='workschedule',
            name='overtime_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4, verbose_name='Переработка (ч)'),
        ),
        migrations.AddField(
            model_name='workschedule',
            name='partial',
            field=models.BooleanField(default=False, verbose_name='Неполная смена'),
        ),
    ]
