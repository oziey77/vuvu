# Generated by Django 4.2.15 on 2024-09-06 05:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_alter_user_last_transacted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_transacted',
            field=models.DateField(default=datetime.date(2024, 9, 6)),
        ),
    ]