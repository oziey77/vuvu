# Generated by Django 4.2.15 on 2024-10-14 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminbackend', '0009_cablebackend'),
    ]

    operations = [
        migrations.CreateModel(
            name='VuvuStory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('youtube_id', models.CharField(max_length=20)),
            ],
        ),
    ]