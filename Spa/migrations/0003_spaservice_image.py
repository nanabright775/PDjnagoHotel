# Generated by Django 5.0.4 on 2024-08-07 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Spa', '0002_remove_spabooking_full_name_spabooking_for_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='spaservice',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='media/'),
        ),
    ]
