from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse


from triviagame.models import Game, Page, Response, Team, Question
from triviagame.forms import CsrfDummyForm
from triviagame.views import compute_leaderboard_data
from .forms import SomePageForm, GameForm, PageForm, QuestionForm
from .models import GameHostPermissions


@login_required
def host_home(request):
    hosting = None

    if 'hosting' in request.session:
        hosting_cookie = int(request.session['hosting'])
        try:
            hosting = Game.objects.get(pk=hosting_cookie)
        except Game.DoesNotExist:
            pass
    
    available = GameHostPermissions.objects.filter(
        user=request.user,
        can_host=True,
    )

    return render(request, 'host/home.html', {
        'hosting': hosting,
        'available': [a.game for a in available],
        'uncurse_url': request.build_absolute_uri(reverse('uncurse')),
        'commit': settings.DEPLOYED_COMMIT,
    })


@login_required
def host_join(request, id):
    try:
        permission = GameHostPermissions.objects.get(
            user=request.user,
            game__id=id,
            can_host=True,
        )
    except GameHostPermissions.DoesNotExist:
        return HttpResponseRedirect(reverse('host_home'))

    if request.method == 'POST':
        request.session['hosting'] = permission.game.id
        return HttpResponseRedirect(reverse('pages'))

    return render(request, 'host/host.html', {
        'game': permission.game,
    })


@login_required
def toggle_game(request):
    if 'hosting' not in request.session:
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])

    if request.method == 'POST':
        form = CsrfDummyForm(request.POST)
        if form.is_valid():
            hosting.open = not hosting.open
            hosting.save()
            if hosting.open:
                return HttpResponseRedirect(reverse('pages'))
    
    return HttpResponseRedirect(reverse('host_home'))


@login_required
def pages(request):
    if 'hosting' not in request.session:
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])
    player_join_url = request.build_absolute_uri(
        reverse('join_game', args=(hosting.id, hosting.passcode)))

    return render(request, 'host/pages.html', {
        'hosting': hosting,
        'player_join_url': player_join_url,
    })


@login_required
def toggle_page(request, open):
    if 'hosting' not in request.session:
        return HttpResponseRedirect(reverse('host_home'))

    if request.method == 'POST':
        form = SomePageForm(request.POST)
        if form.is_valid():
            page = Page.objects.get(pk=form.cleaned_data['page'])
            page.open = open
            page.save()
    
    return HttpResponseRedirect(reverse('pages'))


@login_required
def score_page(request, page_id):
    if 'hosting' not in request.session:
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])
    page = Page.objects.get(pk=page_id, game=hosting)

    if request.method == 'POST':
        form = CsrfDummyForm(request.POST)
        if form.is_valid():
            _record_scores(request.POST)
            return HttpResponseRedirect(reverse('score_page', args=(page.id,)))
        else:
            return HttpResponseBadRequest('failed csrf validation')

    return render(request, 'host/scoring.html', {
        'hosting': hosting,
        'page': page,
        'dummy_form': CsrfDummyForm(),
    })


def _record_scores(post_data):
    incoming_data = {}
    for key in post_data:
        if key[:6] == 'exist_':
            # HTML forms are a hot mess - an unchecked checkbox isn't sent!
            response_id = int(key[6:])
            check_key = f'check_{response_id}'
            value = check_key in post_data
            print(f"{response_id}: {value}")
            incoming_data[response_id] = value

    responses = Response.objects.filter(id__in=incoming_data.keys())
    for r in responses:
        r.graded = True
        r.score = 1 if incoming_data.get(r.id, False) else 0
    Response.objects.bulk_update(responses, fields=['graded', 'score'])


@login_required
def host_leaderboard(request):
    if 'hosting' not in request.session:
        return HttpResponseRedirect(reverse('host_home'))

    hosting = Game.objects.get(pk=request.session['hosting'])

    rounds, ldr_board, gold_medals = compute_leaderboard_data(hosting)

    return render(request, 'host/leaderboard.html', {
        'game': hosting,
        'rounds': rounds,
        'leaderboard': ldr_board,
        'gold_medals': gold_medals,
    })


@login_required
def team_page(request, team_id):
    if 'hosting' not in request.session:
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
# TODO: check edit permission

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

    return render(request, 'editor/new.html', {
        'form': form,
    })


@login_required
def edit_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)

    if request.method == 'POST':
        game_form = GameForm(request.POST, instance=game)
        if game_form.is_valid():
            updated_game = game_form.save()
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

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
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

    if request.method == 'POST':
        page_form = PageForm(request.POST, instance=page)
        if page_form.is_valid():
            updated_page = page_form.save()
            return HttpResponseRedirect(reverse('edit_page', args=(updated_page.id,)))
    else:
        page_form = PageForm(instance=page)

    return render(request, 'editor/page.html', {
        'page': page,
        'page_form': page_form,
    })


@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        if question_form.is_valid():
            updated_question = question_form.save()
            return HttpResponseRedirect(reverse('edit_page', args=(updated_question.page.id,)))
    else:
        question_form = QuestionForm(instance=question)

    return render(request, 'editor/question.html', {
        'question': question,
        'question_form': question_form,
    })
