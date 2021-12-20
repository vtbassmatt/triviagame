from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse


from triviagame.models import Game, Page, Response, Team
from triviagame.forms import CsrfDummyForm
from triviagame.views import compute_leaderboard_data
from .forms import HostGameForm, SomePageForm
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
def host_join(request, id=0, code=None):
    if request.method == 'POST':
        form = HostGameForm(request.POST)
        if form.is_valid():
            _id = form.cleaned_data['id']
            _code = form.cleaned_data['code']
            try:
                desired_game = Game.objects.get(pk=_id, hostkey=_code)
                request.session['hosting'] = desired_game.id
                return HttpResponseRedirect(reverse('host_home'))
            except Game.DoesNotExist:
                form.add_error(None, ValidationError('Could not find that game', code='notfound'))
    else:
        initial = {}
        if id > 0:
            initial['id'] = id
        if code:
            initial['code'] = code
        form = HostGameForm(initial=initial)

    return render(request, 'host/host.html', {
        'form': form,
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
