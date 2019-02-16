# Generated by Django 2.1.5 on 2019-02-14 21:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0032_auto_20190214_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='name',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='group',
            name='nick',
            field=models.CharField(default='New Group', max_length=20),
        ),
        migrations.AddField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='group',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='members', to='users.Profile'),
        ),
        migrations.AlterField(
            model_name='group',
            name='mods',
            field=models.ManyToManyField(blank=True, to='users.Profile'),
        ),
    ]
