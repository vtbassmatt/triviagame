from django.db import IntegrityError
from django.db.models import Sum
from django.forms import ValidationError, HiddenInput
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.crypto import get_random_string

from . import models
from .forms import JoinGameForm, CreateTeamForm, ReJoinTeamForm, CsrfDummyForm


def home(request):
    game = None
    team = None

    if 'game' in request.session:
        game_cookie = int(request.session['game'])
        try:
            game = models.Game.objects.get(pk=game_cookie)
        except models.Game.DoesNotExist:
            del request.session['game']
    
    if 'team' in request.session:
        team_cookie = int(request.session['team'])
        try:
            team = models.Team.objects.get(pk=team_cookie)
        except models.Team.DoesNotExist:
            del request.session['team']

    # if we're somehow in a team from a different game, fix that
    if game and team and team.game != game:
        team = None
        del request.session['team']
    
    # if we're somehow only in a team, fix that
    if team and not game:
        game = team.game
        request.session['game'] = game
    
    return render(request, 'home.html', {
        'game': game,
        'team': team,
        'form': JoinGameForm(),
    })


def uncurse(request):
    # if something bad has happened, this will clear the session
    request.session.clear()
    return HttpResponseRedirect(reverse('home'))


def join_game(request, id=0, code=None):
    game_name = None
    if id > 0:
        try:
            preview_game = models.Game.objects.get(pk=id, passcode=code)
            game_name = preview_game.name
        except models.Team.DoesNotExist:
            pass

    if request.method == 'POST':
        form = JoinGameForm(request.POST)
        if form.is_valid():
            _id = form.cleaned_data['id']
            _code = form.cleaned_data['code']
            try:
                desired_game = models.Game.objects.get(pk=_id, passcode=_code)
                request.session['game'] = desired_game.id
                if 'team' in request.session:
                    del request.session['team']
                return HttpResponseRedirect(reverse('create_team'))
            except models.Game.DoesNotExist:
                form.add_error(None, ValidationError('Could not find that game', code='notfound'))
    else:
        initial = {}
        if id > 0:
            initial['id'] = id
        if code:
            initial['code'] = code
        form = JoinGameForm(initial=initial)
        if game_name:
            # depends on team_name depending on both fields
            form.fields['id'].widget = HiddenInput()
            form.fields['code'].widget = HiddenInput()

    return render(request, 'join.html', {
        'form': form,
        'game_name': game_name,
    })


def create_team(request):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])

    if request.method == 'POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            recovery_code = get_random_string(10, 'ABCDEFGHJKLMNPQRTUVWXYZ2346789')
            team = models.Team(
                game=game,
                name=form.cleaned_data['name'],
                members=form.cleaned_data['members'],
                passcode=recovery_code,
            )
            team.save()
            request.session['team'] = team.id
            return HttpResponseRedirect(reverse('play'))
    else:
        form = CreateTeamForm()

    return render(request, 'create_team.html', {
        'game': game,
        'form': form,
    })


def rejoin_team(request, id=0, code=None):
    team_name = None
    if id > 0:
        try:
            preview_team = models.Team.objects.get(pk=id, passcode=code)
            team_name = preview_team.name
        except models.Team.DoesNotExist:
            pass

    if request.method == 'POST':
        form = ReJoinTeamForm(request.POST)
        if form.is_valid():
            _id = form.cleaned_data['id']
            _code = form.cleaned_data['code']
            try:
                desired_team = models.Team.objects.get(pk=_id, passcode=_code)
                request.session['team'] = desired_team.id
                request.session['game'] = desired_team.game.id
                return HttpResponseRedirect(reverse('play'))
            except models.Team.DoesNotExist:
                form.add_error(None, ValidationError('Could not reconnect that team', code='notfound'))
    else:
        initial = {}
        if id > 0:
            initial['id'] = id
        if code:
            initial['code'] = code
        form = ReJoinTeamForm(initial=initial)
        if team_name:
            # depends on team_name depending on both fields
            form.fields['id'].widget = HiddenInput()
            form.fields['code'].widget = HiddenInput()

    return render(request, 'rejoin.html', {
        'form': form,
        'team_name': team_name,
    })


def play(request):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])
    team = models.Team.objects.get(pk=request.session['team'])

    if not game.open:
        return render(request, 'game/closed.html', {
            'game': game,
            'team': team,
        })

    return render(request, 'game/pages.html', {
        'game': game,
        'team': team,
    })


def answer_sheet(request, page_order):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])
    team = models.Team.objects.get(pk=request.session['team'])

    try:
        page = game.page_set.get(order=page_order)
        if not page.open:
            page = None
    except models.Page.DoesNotExist:
        page = None

    if not game.open or not page:
        return HttpResponseRedirect(reverse('play'))
    
    # if a question has a response for this team, grab it here
    response_objs = models.Response.objects.filter(
        team=team, question__page=page)
    responses = {
        x.question.id: x for x in response_objs
    }
    questions = [
        (q, responses.get(q.id, None)) for q in page.question_set.all()
    ]
    score = response_objs.filter(graded=True).aggregate(Sum('score'))['score__sum']

    return render(request, 'game/answer.html', {
        'game': game,
        'team': team,
        'page': page,
        'questions': questions,
        'unanswered_questions': len(questions) - len(responses),
        'page_score': score,
    })


def accept_answers(request, page_order):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    
    game = models.Game.objects.get(pk=request.session['game'])
    team = models.Team.objects.get(pk=request.session['team'])

    try:
        page = game.page_set.get(order=page_order)
        if not page.open:
            page = None
    except models.Page.DoesNotExist:
        page = None

    if not game.open or not page:
        return HttpResponseRedirect(reverse('play'))

    valid_questions = {q.id: q for q in page.question_set.all()}

    if request.method == 'POST':
        form = CsrfDummyForm(request.POST)
        if form.is_valid():
            _save_responses(request.POST, valid_questions, team)
            return HttpResponseRedirect(reverse('answer_sheet', args=(page_order,)))
        else:
            return HttpResponseBadRequest('failed csrf validation')

    else:
        return HttpResponseRedirect(reverse('answer_sheet', args=(page_order,)))


def _save_responses(post_data, valid_questions, team):
    for key in post_data:
        if key[:9] == 'response_':
            response_question_id = int(key[9:])
            response_value = str(post_data[key]).strip()[:100]
            if response_question_id in valid_questions and response_value:
                try:
                    models.Response.objects.create(
                        question=valid_questions[response_question_id],
                        team=team,
                        value=response_value,
                    )
                except IntegrityError:
                    pass


def delete_answer(request, response_id):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    
    try:
        response = models.Response.objects.get(pk=response_id, graded=False)
    except models.Response.DoesNotExist:
        return HttpResponseRedirect(reverse('play'))
    
    if response.team.id != request.session['team']:
        return HttpResponseNotAllowed()

    if request.method == 'POST':
        form = CsrfDummyForm(request.POST)
        if form.is_valid():
            return_page = response.question.page.order
            response.delete()
            return HttpResponseRedirect(reverse('answer_sheet', args=(return_page,)))
        else:
            return HttpResponseBadRequest('failed csrf validation')

    else:
        form = CsrfDummyForm()

    return render(request, 'game/delete.html', {
        'form': form,
        'response': response,
    })


def leaderboard(request):
    if 'game' not in request.session:
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])
    team = models.Team.objects.get(pk=request.session['team'])

    rounds, ldr_board, gold_medals = compute_leaderboard_data(game)

    return render(request, 'game/leaderboard.html', {
        'game': game,
        'team': team,
        'rounds': rounds,
        'leaderboard': ldr_board,
        'gold_medals': gold_medals,
    })


def compute_leaderboard_data(game):
    # HACK: it should be possible to ask the database to do this,
    # but I'm not smart enough to write the query.
    # We want the sum of scores per team per page.
    responses = (
        models.Response.objects
        .filter(team__game=game, graded=True)
    )
    rounds = [round.order for round in game.page_set.all()] + ['final']
    l_board = { t.name: {r: 0 for r in rounds} for t in game.team_set.all() }
    for r in responses:
        l_board[r.team.name][r.question.page.order] += r.score
        l_board[r.team.name]['final'] += r.score
    
    # now we want a list of lists, sorted by final score
    final_board = [[team_name] + list(rest.values()) for team_name, rest in l_board.items()]
    final_board.sort(key=lambda line: line[-1], reverse=True)

    # find first place winners
    gold_medals = []
    if len(final_board) > 0:
        top_score = final_board[0][-1]
        if top_score:
            gold_medals = [line[0] for line in final_board if line[-1] == top_score]

    return rounds, final_board, gold_medals
