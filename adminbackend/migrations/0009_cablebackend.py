# Generated by Django 4.2.15 on 2024-10-05 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminbackend', '0008_alter_electricitybackend_active_backend'),
    ]

    operations = [
        migrations.CreateModel(
            name='CableBackend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Main', max_length=10)),
                ('active_backend', models.CharField(choices=[('9Payment', '9Payment')], default='9Payment', max_length=15)),
            ],
        ),
    ]
