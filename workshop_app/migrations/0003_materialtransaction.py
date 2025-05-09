# Generated by Django 4.2.20 on 2025-05-01 16:23

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('workshop_app', '0002_material_serial_number_materialentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, help_text='Amount used or returned', max_digits=10)),
                ('transaction_type', models.CharField(choices=[('consumption', 'Consumption'), ('return', 'Return')], max_length=20)),
                ('transaction_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('job_reference', models.CharField(blank=True, help_text='Optional job reference', max_length=100)),
                ('operator_name', models.CharField(blank=True, help_text='Name of the person performing the transaction', max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='workshop_app.material')),
            ],
            options={
                'ordering': ['-transaction_date'],
            },
        ),
    ]
