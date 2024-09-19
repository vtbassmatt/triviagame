from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Q
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django_htmx.http import trigger_client_event, HttpResponseClientRedirect
from guardian.ctypes import get_content_type
from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_objects_for_user,
    get_users_with_perms,
)
from guardian.utils import get_group_obj_perms_model, get_user_obj_perms_model

from game.models import Game, Page, Response, Team, Question
from game.views import compute_leaderboard_data
from .forms import GameForm, GameHostForm, PageForm, QuestionForm
from .view_utils import (
    can_host_game, can_view_game,
    can_edit_game, can_edit_page, can_edit_question
)

User = get_user_model()


class HttpResponseConflict(HttpResponse):
    status_code = HTTPStatus.CONFLICT


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

    return render(request, template, {
        'user': request.user,
        'games': games,
        'uncurse_url': request.build_absolute_uri(reverse('uncurse')),
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
def toggle_game(request, game_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    game = request.game

    game.open = not game.open
    game.save()
    if game.open:
        messages.success(request, "You opened the game.")
    else:
        messages.success(request, "You closed the game.")
    
    response = render(request, 'host/_toggle_game.html', {
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
    player_join_url = request.build_absolute_uri(
        reverse('join_game', args=(request.game.id, request.game.passcode)))
    game_hosts = get_users_with_perms(
        request.game,
        with_superusers=True,
        with_group_users=True,
        only_with_perms_in=['view_game', 'host_game', 'edit_game'],
    )

    template = 'host/pages.html'

    if request.htmx and request.htmx.trigger_name == 'pagesList':
        template = 'host/_pages_list.html'

    return render(request, template, {
        'user': request.user,
        'game': request.game,
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
    score = int(request.POST['score'])
    response.score = score
    response.graded = True
    response.save()

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

    return render(request, 'host/team.html', {
        'game': request.game,
        'team': team,
        'rejoin_link': request.build_absolute_uri(
            reverse('rejoin_team', args=(team.id, team.passcode))),
    })


# Editor views

@login_required
def new_game(request):
    if not request.user.has_perm('game.add_game'):
        return HttpResponseForbidden("Not authorized to create games.")

    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                game = form.save()
                assign_perm('host_game', request.user, game)
                assign_perm('change_game', request.user, game)
                assign_perm('view_game', request.user, game)
            return HttpResponseRedirect(reverse('edit_game', args=(game.id,)))
    
    else:
        form = GameForm()

    return render(request, 'editor/new_game.html', {
        'form': form,
    })


@login_required
@can_edit_game
def edit_game(request, game_id):
    game = request.game
    game_hosts = get_users_with_perms(
        game,
        with_superusers=True,
        with_group_users=True,
        only_with_perms_in=['view_game', 'host_game', 'edit_game'],
    )

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
        'game_hosts': game_hosts,
        'game_form': game_form,
    })


def _get_available_new_game_hosts(game: Game):
    # The code looks weird because this was copied from Django Guardian's
    # source and I wanted to minimize changes. This inverts the meaning of
    # get_users_with_perms to get users WITHOUT perm (`exlude` rather than
    # `filter`). I later realized you can't remove permissions easily
    # from a superuser or someone in a group, so a few more changes
    # snuck in.
    # original: https://github.com/django-guardian/django-guardian/blob/55beb9893310b243cbd6f578f9665c3e7c76bf96/guardian/shortcuts.py#L241
    with_group_users = False
    only_with_perms_in = ['view_game', 'host_game', 'edit_game']

    ctype = get_content_type(game)
    user_model = get_user_obj_perms_model(game)
    related_name = user_model.user.field.related_query_name()
    if user_model.objects.is_generic():
        user_filters = {
            '%s__content_type' % related_name: ctype,
            '%s__object_pk' % related_name: game.pk,
        }
    else:
        user_filters = {'%s__content_object' % related_name: game}
    qset = Q(**user_filters)

    if only_with_perms_in is not None:
        permission_ids = Permission.objects.filter(content_type=ctype, codename__in=only_with_perms_in).values_list('id', flat=True)
        qset &= Q(**{
            '%s__permission_id__in' % related_name: permission_ids,
            })
        
    if with_group_users:
        group_model = get_group_obj_perms_model(game)
        if group_model.objects.is_generic():
            group_obj_perm_filters = {
                'content_type': ctype,
                'object_pk': game.pk,
            }
        else:
            group_obj_perm_filters = {
                'content_object': game,
            }
        if only_with_perms_in is not None:
            group_obj_perm_filters.update({
                'permission_id__in': permission_ids,
                })
        group_ids = set(group_model.objects.filter(**group_obj_perm_filters).values_list('group_id', flat=True).distinct())
        qset = qset | Q(groups__in=group_ids)

    return (
        get_user_model().objects
        # only active users
        .filter(is_active=True)
        # exclude superusers
        .exclude(is_superuser=True)
        # all the above stuff
        .exclude(qset)
        .distinct()
    )


@login_required
@can_edit_game
def edit_game_hosts(request, game_id):
    game = request.game
    game_hosts = get_users_with_perms(
        game,
        with_superusers=True,
        only_with_perms_in=['view_game', 'host_game', 'edit_game'],
    )
    possible_new_game_hosts = _get_available_new_game_hosts(game)

    if request.method == 'POST':
        game_host_form = GameHostForm(request.POST, queryset=possible_new_game_hosts)
        if game_host_form.is_valid():
            # we allow adding hosts to an open game
            new_host = game_host_form.cleaned_data['host']
            with transaction.atomic():
                assign_perm('host_game', new_host, game)
                assign_perm('change_game', new_host, game)
                assign_perm('view_game', new_host, game)

            if request.htmx:
                Redirect = HttpResponseClientRedirect
            else:
                Redirect = HttpResponseRedirect
                messages.success(request, f"Added host '{new_host}'.")       

            return Redirect(reverse('edit_game_hosts', args=(game.id,)))
    else:
        game_host_form = GameHostForm(queryset=possible_new_game_hosts)

    return render(request, 'editor/hosts.html', {
        'game': game,
        'game_hosts': game_hosts,
        'game_host_form': game_host_form,
        'any_hosts_to_add': len(possible_new_game_hosts) > 0,
    })


@login_required
@can_edit_game
@require_http_methods(["DELETE"])
def hx_remove_game_host(request, game_id, user_id):
    # this is an HTMX-only view
    if not request.htmx:
        return HttpResponseBadRequest("expected HTMX request")

    game = request.game
    user_to_remove = get_object_or_404(User, pk=user_id)
    removable_host = get_users_with_perms(
        game,
        only_with_perms_in=['view_game', 'host_game', 'edit_game'],
    ).filter(id=user_to_remove.id).first()
    friendly_name = user_to_remove.get_full_name() or user_to_remove.username

    if game.open:
        return HttpResponse(f'Cannot remove {friendly_name} as a host while the game is open.')

    if removable_host:
        with transaction.atomic():
            remove_perm('host_game', removable_host, game)
            remove_perm('change_game', removable_host, game)
            remove_perm('view_game', removable_host, game)
        redo_link = reverse('edit_game_hosts', args=(game.id,))
        hx_vals = f'{{"host":{user_to_remove.id}}}'
        return HttpResponse(f'{friendly_name} was removed as host. <a class="btn btn-sm btn-outline-primary" hx-post="{redo_link}" hx-vals=\'{hx_vals}\'>Undo</a> to add them back.')
    else:
        return HttpResponse(f'Tried but failed to remove {friendly_name}.')
    
    


@login_required
@can_edit_game
def new_page(request, game_id):
    game = request.game

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
@can_edit_page
def edit_page(request, page_id):
    page = request.page

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
@can_edit_page
def delete_page(request, page_id):
    page = request.page

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
@can_edit_page
@require_POST
def page_move(request, page_id, delta):
    # this assertion comes from urls.py
    assert delta == 1 or delta == -1

    page = request.page
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
@can_edit_page
def new_question(request, page_id):
    page = request.page

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
@can_edit_question
def edit_question(request, question_id):
    question = request.question

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
@can_edit_question
def delete_question(request, question_id):
    question = request.question

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
@can_edit_question
@require_POST
def question_move(request, question_id, delta):
    # this assertion comes from urls.py
    assert delta == 1 or delta == -1

    question = request.question
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
