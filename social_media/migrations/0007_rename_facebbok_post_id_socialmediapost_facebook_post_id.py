# Generated by Django 5.0.4 on 2024-08-27 16:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social_media', '0006_socialmediapost_facebbok_post_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='socialmediapost',
            old_name='facebbok_post_id',
            new_name='facebook_post_id',
        ),
    ]
