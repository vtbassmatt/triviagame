from django.contrib.auth import get_user_model
from django.db import models

from triviagame.models import Game


class GameHostPermissions(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    can_view = models.BooleanField()
    can_host = models.BooleanField()
    can_edit = models.BooleanField()

    def __str__(self):
        perm_bits = "".join([
            "E" if self.can_edit else "-",
            "H" if self.can_host else "-",
            "V" if self.can_view else "-",
        ])
        return f"{self.user}@{self.game}: {perm_bits}"
