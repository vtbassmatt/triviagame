from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps

from game.models import Game


def _has_any_perm(perms_list):
    def decorator(view):
        @wraps(view)
        def inner(request, *args, **kwargs):
            game_id = kwargs['game_id']
            game = Game.objects.get(pk=game_id)
            if not any([request.user.has_perm(perm, game) for perm in perms_list]):
                if request.htmx:
                    messages.error(request, "You don't have permission to do that.")
                return HttpResponseForbidden("You don't have permission to do that.")
            request.game = game
            return view(request, *args, **kwargs)
        return inner
    return decorator


can_host_game = _has_any_perm(['game.host_game'])
can_host_game.__doc__ = "Decorator to require host_game permissions (assumes game_id in the view args)"

can_view_game = _has_any_perm(['game.view_game', 'game.host_game'])
can_view_game.__doc__ = "Decorator to require view_game or host_game permissions (assumes game_id in the view args)"
