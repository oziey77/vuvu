# Generated by Django 4.2.15 on 2024-08-27 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_cashback'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashback',
            name='message',
            field=models.CharField(default='No feedback', max_length=100),
        ),
    ]