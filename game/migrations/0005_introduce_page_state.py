# Generated by Django 4.1.2 on 2022-10-18 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_remove_hostkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='state',
            field=models.IntegerField(choices=[(0, 'Locked'), (1, 'Open'), (2, 'Scoring')], default=0),
        ),
    ]
