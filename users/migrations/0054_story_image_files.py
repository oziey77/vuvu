# Generated by Django 4.1.7 on 2024-10-31 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0053_storyimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='image_files',
            field=models.FileField(blank=True, null=True, upload_to='stories_images_zip'),
        ),
    ]