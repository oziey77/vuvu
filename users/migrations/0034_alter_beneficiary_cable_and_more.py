# Generated by Django 4.2.15 on 2024-09-30 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_alter_beneficiary_cable_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beneficiary',
            name='cable',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='beneficiary',
            name='electricity',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='beneficiary',
            name='telecomms',
            field=models.JSONField(default=list),
        ),
    ]