# Generated by Django 4.1.2 on 2022-10-24 20:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('host', '0002_alter_gamehostpermissions_options'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GameHostPermissions',
        ),
    ]
