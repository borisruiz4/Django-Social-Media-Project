# Generated by Django 2.1.5 on 2019-02-16 03:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0036_auto_20190215_2151'),
        ('blog', '0030_request_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Group'),
        ),
    ]
