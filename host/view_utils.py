from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps

from game.models import Game, Page, Question


def _can_edit_obj(klass, pk_name, path_to_game):
    "Example: klass = Question, pk_name = question_id, path_to_game = page.game"
    def decorator(view):
        @wraps(view)
        def inner(request, *args, **kwargs):
            obj_id = kwargs[pk_name]
            obj = klass.objects.get(pk=obj_id)

            game = obj
            for part in path_to_game.split('.'):
                game = getattr(game, part)

            if not request.user.has_perm('game.change_game', game):
                if request.htmx:
                    messages.error(request, "You don't have permission to do that.")
                return HttpResponseForbidden("You don't have permission to do that.")
            
            setattr(request, klass.__name__.lower(), obj)
            return view(request, *args, **kwargs)
        return inner
    return decorator


can_edit_question = _can_edit_obj(Question, 'question_id', 'page.game')
can_edit_question.__doc__ = """Decorator to require `edit_game` permissions on an associated question.

Assumes `question_id` is in the view args, and puts a `question` attribute on the request."""

can_edit_page = _can_edit_obj(Page, 'page_id', 'game')
can_edit_page.__doc__ = """Decorator to require `edit_game` permissions on an associated page.

Assumes `page_id` is in the view args, and puts a `page` attribute on the request."""


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


can_edit_game = _has_any_perm(['game.change_game'])
can_edit_game.__doc__ = """Decorator to require `edit_game` permissions.

Assumes `game_id` is in the view args, and puts a `game` attribute on the request."""

can_host_game = _has_any_perm(['game.host_game'])
can_host_game.__doc__ = """Decorator to require `host_game` permissions.

Assumes `game_id` is in the view args, and puts a `game` attribute on the request."""

can_view_game = _has_any_perm(['game.view_game', 'game.host_game', 'game.edit_game'])
can_view_game.__doc__ = """Decorator to require `view_game`, `host_game`, or `edit_game` permissions.

Assumes `game_id` is in the view args, and puts a `game` attribute on the request."""


def build_absolute_uri(request, relative_url):
    # on fly.io, we see the request proxied in over HTTP, but we want to
    # generate HTTPS links. but if we do that blindly, then in debug
    # mode, we generate https links that don't work. this is a decent
    # hack.
    full_url = request.build_absolute_uri(relative_url)
    if not settings.DEBUG:
        full_url = full_url.replace('http://', 'https://')
    return full_url
