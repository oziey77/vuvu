# Generated by Django 4.2.15 on 2024-10-04 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminbackend', '0007_electricitybackend'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electricitybackend',
            name='active_backend',
            field=models.CharField(choices=[('9Payment', '9Payment')], default='9Payment', max_length=15),
        ),
    ]