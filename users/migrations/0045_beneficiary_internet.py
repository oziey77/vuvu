# Generated by Django 4.2.15 on 2024-10-15 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0044_story'),
    ]

    operations = [
        migrations.AddField(
            model_name='beneficiary',
            name='internet',
            field=models.JSONField(default=list),
        ),
    ]