# Generated by Django 2.1.5 on 2019-02-14 20:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_auto_20190214_1626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='members', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='group',
            name='mods',
            field=models.ManyToManyField(blank=True, related_name='mods', to=settings.AUTH_USER_MODEL),
        ),
    ]
