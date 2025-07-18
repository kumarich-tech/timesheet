from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_department_partial_day_rate_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название шаблона')),
                ('sequence', models.JSONField(verbose_name='Последовательность смен')),
            ],
            options={
                'verbose_name': 'Шаблон графика',
                'verbose_name_plural': 'Шаблоны графиков',
            },
        ),
    ]
