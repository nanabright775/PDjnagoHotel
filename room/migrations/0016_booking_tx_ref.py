# Generated by Django 5.0.4 on 2024-06-02 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0015_alter_payment_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='tx_ref',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
