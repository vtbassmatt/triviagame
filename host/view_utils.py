from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps

from game.models import Game, Page, Question


def can_edit_question(view):
    @wraps(view)
    def inner(request, *args, **kwargs):
        question_id = kwargs['question_id']
        question = Question.objects.get(pk=question_id)
        if not request.user.has_perm('game.change_game', question.page.game):
            if request.htmx:
                messages.error(request, "You don't have permission to do that.")
            return HttpResponseForbidden("You don't have permission to do that.")
        request.question = question
        return view(request, *args, **kwargs)
    return inner


def can_edit_page(view):
    @wraps(view)
    def inner(request, *args, **kwargs):
        page_id = kwargs['page_id']
        page = Page.objects.get(pk=page_id)
        if not request.user.has_perm('game.change_game', page.game):
            if request.htmx:
                messages.error(request, "You don't have permission to do that.")
            return HttpResponseForbidden("You don't have permission to do that.")
        request.page = page
        return view(request, *args, **kwargs)
    return inner


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
can_edit_game.__doc__ = "Decorator to require edit_game permissions (assumes game_id in the view args)"

can_host_game = _has_any_perm(['game.host_game'])
can_host_game.__doc__ = "Decorator to require host_game permissions (assumes game_id in the view args)"

can_view_game = _has_any_perm(['game.view_game', 'game.host_game', 'game.edit_game'])
can_view_game.__doc__ = "Decorator to require view_game, host_game, or edit_game permissions (assumes game_id in the view args)"
