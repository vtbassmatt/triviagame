from http import HTTPStatus
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    QueryDict,
)
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import trigger_client_event, HttpResponseClientRefresh
from guardian.shortcuts import (
    get_objects_for_user,
    get_users_with_perms,
)

from game.models import Game, Page, Response, Team
from game.views import compute_leaderboard_data
from host.forms import TeamForm
from host.view_utils import (
    can_host_game, can_view_game, build_absolute_uri,
)

User = get_user_model()


__all__ = [
    'host_home',
    'host_confirm_logout',
    'update_game_state',
    'pages',
    'set_page_state',
    'score_page',
    'assign_score',
    'host_leaderboard',
    'team_page',
    'hx_edit_team',
]


class HttpResponseNoContent(HttpResponse):
    status_code = HTTPStatus.NO_CONTENT


@login_required
def host_home(request):
    all_games = Game.objects.order_by('-last_edit_time')
    
    # TODO: might need these if perf suffers
    # (from guardian.core import ObjectPermissionChecker)
    # checker = ObjectPermissionChecker(request.user)
    # checker.prefetch_perms(all_games)

    games = get_objects_for_user(
        request.user,
        'game.view_game',
        all_games,
    )

    template = 'host/home.html'

    if request.htmx and request.htmx.trigger_name == 'gamesList':
        template = 'host/_games_list.html'
    
    uncurse_url = build_absolute_uri(
        request,
        reverse('uncurse'),
    )

    return render(request, template, {
        'user': request.user,
        'games': games,
        'uncurse_url': uncurse_url,
    })


@login_required
def host_confirm_logout(request):
    return render(
        request,
        'registration/confirm_logout.html',
        {}
    )


@login_required
@can_host_game
@require_POST
def update_game_state(request, game_id, new_state):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    game = request.game

    if game.id != game_id:
        print("game.id != game_id")
        ... # TODO, this means something has gone wrong

    if new_state in Game.GameState.values:
        game.state = new_state
        game.save()

    messages.success(
        request,
        {
            Game.GameState.CLOSED: "You closed the game.",
            Game.GameState.ACCEPTING_TEAMS: "You opened the game. New teams can join.",
            Game.GameState.NO_NEW_TEAMS: "Game is open, but no new teams can join.",
        }[game.state],
    )
    
    response = render(request, 'host/_update_game_state.html', {
        'user': request.user,
        'game': game,
    })
    # tell the page that game state has updated
    trigger_client_event(
        response,
        'hostedGameStateUpdated',
        True,
    )

    return response


@login_required
@can_view_game
def pages(request, game_id):
    player_join_url = build_absolute_uri(
        request,
        reverse('join_game', args=(request.game.id, request.game.passcode))
    )

    game_hosts = get_users_with_perms(
        request.game,
        with_superusers=True,
        with_group_users=True,
        only_with_perms_in=['view_game', 'host_game', 'edit_game'],
    )

    game_max_points = (
        request.game.page_set
        .filter(is_hidden=False)
        .aggregate(points=Sum('question__possible_points'))
    ).get('points', None) or 0
    game_hidden_points = (
        request.game.page_set
        .filter(is_hidden=True)
        .aggregate(points=Sum('question__possible_points'))
    ).get('points', None) or 0

    template = 'host/pages.html'

    if request.htmx and request.htmx.trigger_name == 'pagesList':
        template = 'host/_pages_list.html'

    return render(request, template, {
        'user': request.user,
        'game': request.game,
        'game_max_points': game_max_points,
        'game_hidden_points': game_hidden_points,
        'game_hosts': game_hosts,
        'player_join_url': player_join_url,
    })


@login_required
@can_host_game
@require_POST
def set_page_state(request, game_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    if 'page' not in request.POST:
        return HttpResponseBadRequest("expected page id")
    
    if 'state' not in request.POST:
        return HttpResponseBadRequest("expected new page state")

    page_id = int(request.POST['page'])
    page = get_object_or_404(Page, pk=page_id)
    new_state = Page.PageState[request.POST['state']]
    page.state = new_state
    page.save()
    messages.success(request, f"{page.title} is now {page.state.label}.")

    response = HttpResponseNoContent()
    # report that some page's state has updated
    return trigger_client_event(
        response,
        'pageStateUpdated',
        {'page': page_id},
    )


@login_required
@can_host_game
def score_page(request, game_id, page_id):
    # TODO: viewers can see this page but can't interact
    page = request.game.page_set.get(pk=page_id)

    return render(request, 'host/scoring.html', {
        'game': request.game,
        'page': page,
    })

@login_required
@can_host_game
@require_POST
def assign_score(request, game_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    if 'response' not in request.POST:
        return HttpResponseBadRequest("expected response id")
    
    if 'score' not in request.POST:
        return HttpResponseBadRequest("expected score")

    response_id = int(request.POST['response'])
    response = get_object_or_404(Response, pk=response_id)

    if response.question.page.is_scoring:
        score = int(request.POST['score'])
        if score >= 0:
            response.score = score
            response.graded = True
        else:
            response.score = 0
            response.graded = False
        response.save()
    else:
        return HttpResponseClientRefresh()

    return render(request, 'host/_question_score.html', {
        'game': request.game,
        'question': response.question,
    })


@login_required
@can_view_game
def host_leaderboard(request, game_id):
    game = request.game

    rounds, ldr_board, gold_medals = compute_leaderboard_data(game)

    return render(request, 'host/leaderboard.html', {
        'game': game,
        'rounds': rounds,
        'teams': { t.name: t.members for t in game.team_set.all() },
        'leaderboard': ldr_board,
        'gold_medals': gold_medals,
    })


@login_required
@can_view_game
def team_page(request, game_id, team_id):
    team = Team.objects.get(pk=team_id)

    template = 'host/team.html'
    responses = (
        Response.objects
        .filter(team=team)
        .order_by('question__page__order', 'question__order')
    )
    if request.htmx:
        template = 'host/_team_fragment.html'
        responses = None
    
    rejoin_link = build_absolute_uri(
        request,
        reverse('rejoin_team', args=(team.id, team.passcode)),
    )

    return render(request, template, {
        'game': request.game,
        'team': team,
        'rejoin_link': rejoin_link,
        'responses': responses,
    })


def _get_PUT_data(request):
    # modeled after https://github.com/django/django/blob/901ec7a217d174b25ac008c9c385928a36f870d1/django/http/request.py#L355
    if request.method != "PUT":
        return QueryDict(encoding=request._encoding)
    
    if request.content_type == "multipart/form-data":
        if hasattr(request, "_body"):
            # Use already read data
            data = BytesIO(request._body)
        else:
            data = request

        # no try/catch here since we don't do any local error handling
        put_, _ = request.parse_file_upload(request.META, data)
        return put_

    elif request.content_type == "application/x-www-form-urlencoded":
        # According to RFC 1866, the "application/x-www-form-urlencoded"
        # content type does not have a charset and should be always treated
        # as UTF-8.
        if request._encoding is not None and request._encoding.lower() != "utf-8":
            raise BadRequest(
                "HTTP requests with the 'application/x-www-form-urlencoded' "
                "content type must be UTF-8 encoded."
            )
        return QueryDict(request.body, encoding="utf-8")
        
    else:
        return QueryDict(encoding=request._encoding)


@login_required
@can_view_game
def hx_edit_team(request, game_id, team_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    team = get_object_or_404(Team, pk=team_id, game=request.game)
    initial = {
        key: getattr(team, key, '') for key in ['name', 'members']
    }

    if request.method == 'PUT':
        data = _get_PUT_data(request)
        form = TeamForm(data, initial=initial)
        if form.is_valid():
            team.name = form.cleaned_data['name']
            team.members = form.cleaned_data['members']
            team.save()
            return render(request, 'host/_team_fragment.html', {
                'game': request.game,
                'team': team,
            })
    
    else:
        form = TeamForm(initial=initial)

    return render(request, 'host/_team_form.html', {
        'form': form,
        'put_url': reverse('edit_team', args=(game_id, team_id)),
        'get_url': reverse('team_page', args=(game_id, team_id)),
    })
