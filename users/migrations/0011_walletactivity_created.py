# Generated by Django 4.2.15 on 2024-08-24 11:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_walletactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='walletactivity',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
