# Generated by Django 4.2.15 on 2024-09-04 03:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneTimeDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accountNumber', models.CharField(max_length=10)),
                ('accountName', models.CharField(max_length=50)),
                ('transactionAmount', models.IntegerField()),
                ('settledAmount', models.IntegerField(default=0)),
                ('accountID', models.CharField(max_length=28)),
                ('reference', models.CharField(max_length=20)),
                ('bankName', models.CharField(choices=[('SafeHaven MFB', 'SafeHaven MFB')], default='SafeHaven MFB', max_length=20)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Failed', 'Failed'), ('Completed', 'Completed')], default='Pending', max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]