# Generated by Django 2.1.5 on 2019-02-27 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0041_group_hidden'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='hidden',
        ),
        migrations.AddField(
            model_name='group',
            name='anonymity',
            field=models.CharField(choices=[('1', 'None'), ('2', 'Hide Owner and Member Identities')], default='1', max_length=1),
        ),
    ]
