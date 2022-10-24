from http import HTTPStatus


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event


from game.models import Game, Page, Response, Team, Question
from game.views import compute_leaderboard_data
from .forms import GameForm, PageForm, QuestionForm
from .models import GameHostPermissions


class HttpResponseConflict(HttpResponse):
    status_code = HTTPStatus.CONFLICT


class HttpResponseNoContent(HttpResponse):
    status_code = HTTPStatus.NO_CONTENT


@login_required
def host_home(request):
    hosting = None

    if 'hosting' in request.session:
        hosting_cookie = int(request.session['hosting'])
        try:
            hosting = Game.objects.get(pk=hosting_cookie)
        except Game.DoesNotExist:
            pass
    
    editable = GameHostPermissions.objects.filter(
        user=request.user,
        can_edit=True,
    ).order_by(
        '-game__last_edit_time',
    )

    hostable = GameHostPermissions.objects.filter(
        user=request.user,
        can_host=True,
        can_edit=False,
    ).order_by(
        '-game__last_edit_time',
    )

    template = 'host/home.html'

    if request.htmx and request.htmx.trigger_name == 'gamesList':
        template = 'host/_games_list.html'

    return render(request, template, {
        'hosting': hosting,
        'hostable': [h.game for h in hostable],
        'editable': [e.game for e in editable],
        'uncurse_url': request.build_absolute_uri(reverse('uncurse')),
    })


@login_required
def host_join(request, game_id):
    try:
        permission = GameHostPermissions.objects.get(
            Q(user=request.user),
            Q(game__id=game_id),
            Q(can_host=True) | Q(can_edit=True),
        )
    except GameHostPermissions.DoesNotExist:
        messages.error(request, "Can't host that game.")
        return HttpResponseRedirect(reverse('host_home'))

    if request.method == 'POST':
        request.session['hosting'] = permission.game.id
        return HttpResponseRedirect(reverse('pages', args=(game_id,)))

    return render(request, 'host/host.html', {
        'game': permission.game,
    })


@login_required
@require_POST
def toggle_game(request, game_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    hosting = Game.objects.get(pk=game_id)
    if hosting.gamehostpermissions_set.filter(
        user=request.user,
        can_host=True,
    ).count() == 0:
        messages.error(request, "You don't have permission to toggle game state.")
        return HttpResponseForbidden()

    hosting.open = not hosting.open
    hosting.save()
    if hosting.open:
        messages.success(request, "You opened the game.")
    else:
        messages.success(request, "You closed the game.")
    
    response = render(request, 'host/_toggle_game.html', {
        'hosting': hosting,
    })
    # tell the page that game state has updated
    trigger_client_event(
        response,
        'hostedGameStateUpdated',
        True,
    )

    return response


@login_required
def pages(request, game_id):
    hosting = Game.objects.get(pk=game_id)
    if hosting.gamehostpermissions_set.filter(
        user=request.user,
        can_host=True,
    ).count() == 0:
        messages.error(request, "You don't have permission to view those pages.")
        return HttpResponseForbidden()

    player_join_url = request.build_absolute_uri(
        reverse('join_game', args=(hosting.id, hosting.passcode)))

    template = 'host/pages.html'

    if request.htmx and request.htmx.trigger_name == 'pagesList':
        template = 'host/_pages_list.html'

    return render(request, template, {
        'hosting': hosting,
        'player_join_url': player_join_url,
    })


@login_required
@require_POST
def set_page_state(request):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    if 'hosting' not in request.session:
        _flash_not_hosting(request)
        return HttpResponseClientRedirect(reverse('host_home'))
    
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
def score_page(request, game_id, page_id):
    hosting = Game.objects.get(pk=game_id)
    if hosting.gamehostpermissions_set.filter(
        user=request.user,
        can_host=True,
    ).count() == 0:
        messages.error(request, "You don't have permission to score that game.")
        return HttpResponseForbidden()

    page = hosting.page_set.get(pk=page_id)

    return render(request, 'host/scoring.html', {
        'hosting': hosting,
        'page': page,
    })

@login_required
@require_POST
def assign_score(request, game_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    hosting = Game.objects.get(pk=game_id)
    if hosting.gamehostpermissions_set.filter(
        user=request.user,
        can_host=True,
    ).count() == 0:
        messages.error(request, "You don't have permission to score that answer.")
        return HttpResponseForbidden()
    
    if 'response' not in request.POST:
        return HttpResponseBadRequest("expected response id")
    
    if 'score' not in request.POST:
        return HttpResponseBadRequest("expected score")

    response_id = int(request.POST['response'])
    response = get_object_or_404(Response, pk=response_id)
    score = int(request.POST['score'])
    response.score = score
    response.graded = True
    response.save()

    return render(request, 'host/_question_score.html', {
        'hosting': hosting,
        'question': response.question,
    })


@login_required
def host_leaderboard(request):
    if 'hosting' not in request.session:
        _flash_not_hosting(request)
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])

    rounds, ldr_board, gold_medals = compute_leaderboard_data(hosting)

    return render(request, 'host/leaderboard.html', {
        'game': hosting,
        'rounds': rounds,
        'teams': { t.name: t.members for t in hosting.team_set.all() },
        'leaderboard': ldr_board,
        'gold_medals': gold_medals,
    })


@login_required
def team_page(request, team_id):
    if 'hosting' not in request.session:
        _flash_not_hosting(request)
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])
    team = Team.objects.get(pk=team_id)

    return render(request, 'host/team.html', {
        'hosting': hosting,
        'team': team,
        'rejoin_link': request.build_absolute_uri(
            reverse('rejoin_team', args=(team.id,team.passcode))),
    })


# Editor views

@login_required
def new_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                game = form.save()
                perms = GameHostPermissions(
                    game=game,
                    user=request.user,
                    can_view=True,
                    can_host=True,
                    can_edit=True,
                )
                perms.save()
            return HttpResponseRedirect(reverse('edit_game', args=(game.id,)))
    
    else:
        form = GameForm()

    return render(request, 'editor/new_game.html', {
        'form': form,
    })


@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    if not _can_edit_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        game_form = GameForm(request.POST, instance=game)
        if game.open:
            game_form.add_error(None, ValidationError('Cannot edit an open game', code='gamestate'))
        elif game_form.is_valid():
            updated_game = game_form.save()
            messages.success(request, "Game data saved.")
            return HttpResponseRedirect(reverse('edit_game', args=(updated_game.id,)))
    else:
        game_form = GameForm(instance=game)

    return render(request, 'editor/game.html', {
        'game': game,
        'game_form': game_form,
    })


@login_required
def new_page(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    if not _can_edit_game(request.user, game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = PageForm(request.POST)
        if game.open:
            form.add_error(None, ValidationError('Cannot edit an open game', code='gamestate'))
        elif form.is_valid():
            page = form.save(commit=False)
            # connect page to game
            page.game = game
            # find largest page and make this one more
            max_page = game.page_set.last()
            if max_page:
                new_page_order = max_page.order + 1
            else:
                new_page_order = 1
            page.order = new_page_order
            page.save()
            return HttpResponseRedirect(reverse('edit_page', args=(page.id,)))
    
    else:
        form = PageForm()

    return render(request, 'editor/new_page.html', {
        'game': game,
        'form': form,
    })


@login_required
def edit_page(request, page_id):
    page = get_object_or_404(Page, pk=page_id)
    if not _can_edit_game(request.user, page.game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        page_form = PageForm(request.POST, instance=page)
        if page.game.open:
            page_form.add_error(None, ValidationError('Cannot edit an open game', code='gamestate'))
        elif page_form.is_valid():
            updated_page = page_form.save()
            messages.success(request, "Page data saved.")
            return HttpResponseRedirect(reverse('edit_page', args=(updated_page.id,)))
    else:
        page_form = PageForm(instance=page)

    return render(request, 'editor/page.html', {
        'page': page,
        'page_form': page_form,
    })


@login_required
def delete_page(request, page_id):
    page = get_object_or_404(Page, pk=page_id)
    if not _can_edit_game(request.user, page.game):
        return HttpResponseForbidden()

    if request.method in ('POST', 'DELETE'):
        game = page.game
        if game.open:
            return HttpResponseConflict('Cannot edit an open game')
        order = page.order
        with transaction.atomic():
            page.question_set.all().delete()
            page.delete()
            game.page_set.filter(order__gt=order).update(order=F('order') - 1)
        messages.success(request, f"Page {order} deleted.")
        return HttpResponseRedirect(reverse('edit_game', args=(game.id,)))

    return render(request, 'editor/delete_page.html', {
        'page': page,
    })


@login_required
@require_POST
def page_move(request, page_id, delta):
    # this assertion comes from urls.py
    assert delta == 1 or delta == -1

    page = get_object_or_404(Page, pk=page_id)
    if not _can_edit_game(request.user, page.game):
        return HttpResponseForbidden()
    if page.game.open:
        return HttpResponseConflict('Cannot edit an open game')

    max_page = page.game.page_set.last()
    if delta == 1 and page.id == max_page.id:
        raise IndexError
    if delta == -1 and page.order == 1:
        raise IndexError

    try:
        other_page = Page.objects.get(game=page.game, order=page.order + delta)
        with transaction.atomic():
            desired_order = page.order + delta
            placeholder_order = max_page.order + 1
            page.order = placeholder_order
            page.save()
            other_page.order = F('order') - delta
            other_page.save()
            page.order = desired_order
            page.save()
    except Page.DoesNotExist:
        page.order = F('order') + delta
        page.save()
    
    if request.htmx:
        return render(request, 'editor/_page_list.html', {
            'game': page.game,
        })

    return HttpResponseRedirect(reverse('edit_game', args=(page.game.id,)))


@login_required
def new_question(request, page_id):
    page = get_object_or_404(Page, pk=page_id)
    if not _can_edit_game(request.user, page.game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if page.game.open:
            form.add_error(None, ValidationError('Cannot edit an open game', code='gamestate'))
        elif form.is_valid():
            question = form.save(commit=False)
            # connect question to page
            question.page = page
            # find largest question and make this one more
            max_question = page.question_set.last()
            if max_question:
                new_question_order = max_question.order + 1
            else:
                new_question_order = 1
            question.order = new_question_order
            question.save()
            return HttpResponseRedirect(reverse('edit_page', args=(page.id,)))
    
    else:
        form = QuestionForm()

    return render(request, 'editor/new_question.html', {
        'page': page,
        'form': form,
    })


@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if not _can_edit_game(request.user, question.page.game):
        return HttpResponseForbidden()

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        if question.page.game.open:
            question_form.add_error(None, ValidationError('Cannot edit an open game', code='gamestate'))
        elif question_form.is_valid():
            updated_question = question_form.save()
            messages.success(request, "Question data saved.")
            return HttpResponseRedirect(reverse('edit_page', args=(updated_question.page.id,)))
    else:
        question_form = QuestionForm(instance=question)

    return render(request, 'editor/question.html', {
        'question': question,
        'question_form': question_form,
    })


@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if not _can_edit_game(request.user, question.page.game):
        return HttpResponseForbidden()

    if request.method in ('POST', 'DELETE'):
        page = question.page
        if page.game.open:
            return HttpResponseConflict('Cannot edit an open game')
        order = question.order
        with transaction.atomic():
            question.delete()
            page.question_set.filter(order__gt=order).update(order=F('order') - 1)
        messages.success(request, f"Question {order} deleted.")
        return HttpResponseRedirect(reverse('edit_page', args=(page.id,)))

    return render(request, 'editor/delete_question.html', {
        'question': question,
    })


@login_required
@require_POST
def question_move(request, question_id, delta):
    # this assertion comes from urls.py
    assert delta == 1 or delta == -1

    question = get_object_or_404(Question, pk=question_id)
    if not _can_edit_game(request.user, question.page.game):
        return HttpResponseForbidden()
    if question.page.game.open:
        return HttpResponseConflict('Cannot edit an open game')

    max_question = question.page.question_set.last()
    if delta == 1 and question.id == max_question.id:
        raise IndexError
    if delta == -1 and question.order == 1:
        raise IndexError

    try:
        other_question = Question.objects.get(page=question.page, order=question.order + delta)
        with transaction.atomic():
            desired_order = question.order + delta
            placeholder_order = max_question.order + 1
            question.order = placeholder_order
            question.save()
            other_question.order = F('order') - delta
            other_question.save()
            question.order = desired_order
            question.save()
    except Question.DoesNotExist:
        question.order = F('order') + delta
        question.save()
    
    if request.htmx:
        return render(request, 'editor/_question_list.html', {
            'page': question.page,
        })

    return HttpResponseRedirect(reverse('edit_page', args=(question.page.id,)))


def _can_edit_game(user, game):
    return GameHostPermissions.objects.filter(
        game=game,
        user=user,
        can_edit=True,
    ).count() > 0


def _flash_not_hosting(request):
    messages.error(request, "You aren't hosting a game.")
