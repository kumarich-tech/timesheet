from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_scheduletemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalWorkSchedule',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('date', models.DateField()),
                ('shift', models.CharField(max_length=10, choices=[('day', 'День'), ('night', 'Ночь'), ('weekend', 'Выходной'), ('vacation', 'Отпуск'), ('sick', 'Больничный'), ('partial', 'Неполная')])),
                ('history_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.TextField(null=True)),
                ('history_type', models.CharField(max_length=1)),
                ('employee', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.employee')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical work schedule',
                'verbose_name_plural': 'historical work schedules',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
        ),
    ]
