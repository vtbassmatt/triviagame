from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm


from .models import Game


User = get_user_model()

@receiver(post_save, sender=User)
def grant_game_create(sender, **kwargs):

    if kwargs['created']:
        new_user = kwargs['instance']
        assign_perm('game.add_game', new_user)
