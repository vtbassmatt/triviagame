# Generated by Django 4.1.2 on 2022-10-24 19:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_make_games_sortable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='game',
            options={'ordering': ['-last_edit_time'], 'permissions': (('host_game', 'Host game'),)},
        ),
    ]
