# Generated by Django 5.0.4 on 2024-07-26 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0025_booking_full_name_alter_booking_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='room_status',
            field=models.CharField(choices=[('vacant', 'Vacant'), ('occupied', 'Occupied')], default='vacant', max_length=20),
        ),
    ]
