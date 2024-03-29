# Generated by Django 3.2.9 on 2021-11-13 11:45

from django.db import migrations, models
import django.db.models.deletion
from django.utils.crypto import get_random_string
import game.models


# formerly in models.py
def generate_hostkey():
    return get_random_string(20, 'ABCDEFGHJKLMNPQRTUVWXYZ2346789')


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('passcode', models.CharField(default=game.models.generate_passcode, max_length=20)),
                ('hostkey', models.CharField(default=generate_hostkey, max_length=40)),
                ('open', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.SmallIntegerField()),
                ('open', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.game')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.SmallIntegerField()),
                ('question', models.TextField()),
                ('answer', models.TextField(blank=True)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.page')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('members', models.TextField(blank=True)),
                ('passcode', models.CharField(blank=True, max_length=20)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.game')),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('graded', models.BooleanField(default=False)),
                ('score', models.SmallIntegerField(default=0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.question')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.team')),
            ],
            options={
                'ordering': ['question', 'team'],
            },
        ),
        migrations.AddConstraint(
            model_name='response',
            constraint=models.UniqueConstraint(fields=('question', 'team'), name='one_answer_per_team'),
        ),
        migrations.AddConstraint(
            model_name='question',
            constraint=models.UniqueConstraint(fields=('page', 'order'), name='ensure_question_order'),
        ),
        migrations.AddConstraint(
            model_name='page',
            constraint=models.UniqueConstraint(fields=('game', 'order'), name='ensure_page_order'),
        ),
    ]
