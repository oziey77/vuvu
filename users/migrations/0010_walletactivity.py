# Generated by Django 4.2.15 on 2024-08-24 11:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_user_login_attempts_left'),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('Debit', 'Debit'), ('Credit', 'Credit')], max_length=10)),
                ('transaction_type', models.CharField(choices=[('Airtime', 'Airtime'), ('Data', 'Data'), ('Cable', 'Cable'), ('Electricity', 'Electricity'), ('Transfer', 'Transfer'), ('Admin Deposit', 'Admin Deposit'), ('Cashback Withdrwal', 'Cashback Withdrwal'), ('Referral Bonus', 'Referral Bonus')], max_length=20)),
                ('comment', models.CharField(max_length=100)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('balanceBefore', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('balanceAfter', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]