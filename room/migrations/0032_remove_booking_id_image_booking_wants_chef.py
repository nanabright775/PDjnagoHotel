# Generated by Django 5.0.4 on 2025-04-16 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0031_payment_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='id_image',
        ),
        migrations.AddField(
            model_name='booking',
            name='wants_chef',
            field=models.BooleanField(default=False),
        ),
    ]
