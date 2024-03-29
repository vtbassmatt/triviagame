# Generated by Django 4.1.2 on 2022-10-18 12:34

from django.db import migrations

# When this migration runs, PageState looks like this:
#
#   class PageState(models.IntegerChoices):
#       LOCKED = 0      # players cannot see the page at all
#       OPEN = 1        # players can see and answer the page
#       SCORING = 2     # players can see, but not answer, the page

def move_open_to_state(apps, schema_editor):
    Page = apps.get_model('game', 'Page')
    for page in Page.objects.all():
        # False => 0 (LOCKED)
        # True  => 1 (OPEN)
        page.state = 1 if page.open else 0
        page.save()


def move_state_to_open(apps, schema_editor):
    # NOTE: this is destructive in the sense that LOCKED and SCORING both
    # get mapped to False. When the migration is reapplied forwards,
    # False gets mapped to LOCKED only.
    Page = apps.get_model('game', 'Page')
    for page in Page.objects.all():
        # 0 (LOCKED)  => False
        # 1 (OPEN)    => True
        # 2 (SCORING) => False
        page.open = True if page.state == 1 else False
        page.save()


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_introduce_page_state'),
    ]

    operations = [
        migrations.RunPython(move_open_to_state, move_state_to_open),
    ]
