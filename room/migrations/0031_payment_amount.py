# Generated by Django 5.0.4 on 2025-04-15 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0030_remove_booking_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
