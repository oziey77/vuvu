# Generated by Django 4.2.15 on 2024-10-10 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0041_user_completed_offers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='give_away_level',
            field=models.IntegerField(default=1),
        ),
    ]
