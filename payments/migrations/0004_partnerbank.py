# Generated by Django 4.2.15 on 2024-09-11 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_safehavenpaymenttransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnerBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(choices=[('SafeHaven MFB', 'SafeHaven MFB')], default='SafeHaven MFB', max_length=20)),
                ('deposit_charges', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Disabled', 'Disabled')], default='Active', max_length=20)),
            ],
        ),
    ]
