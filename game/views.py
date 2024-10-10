import random

from django.contrib import messages
from django.db import Error as DjangoDbError
from django.forms import ValidationError, HiddenInput
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django_htmx.http import HttpResponseClientRedirect

from . import models
from .forms import JoinGameForm, CreateTeamForm, ReJoinTeamForm


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
    })


def healthcheck(request):
    return render(
        request,
        'healthcheck.txt',
        {},
        content_type='text/plain'
    )


def uncurse(request):
    # if something bad has happened, this will clear the session
    request.session.clear()
    messages.debug(request, "Deleted your session. That should clear things up.")
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
        _flash_not_in_game(request)
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])

    if request.method == 'POST':
        partial_team = models.Team(game=game, passcode=get_random_string(10, 'ABCDEFGHJKLMNPQRTUVWXYZ2346789'))
        form = CreateTeamForm(request.POST, instance=partial_team)
        if form.is_valid():
            try:
                # because the CreateTeamForm doesn't include every field, `team`
                # gets excluded from validation checks - we must explicitly
                # validate uniques on the instance and only exclude the id
                form.instance.validate_unique(exclude=['id',])
                team = form.save()
                request.session['team'] = team.id
                return HttpResponseRedirect(reverse('play'))
            except ValidationError as e:
                form.add_error(None, e)
            except DjangoDbError as e:
                form.add_error('', ValidationError(e, code='database'))

    else:
        form = CreateTeamForm()

    return render(request, 'create_team.html', {
        'game': game,
        'form': form,
        'sample_team_name': random.choice(CreateTeamForm.TEAM_NAME_IDEAS),
    })


def rejoin_team(request, id=0, code=None):
    team_name = None
    team_members = None

    if id > 0:
        try:
            preview_team = models.Team.objects.get(pk=id, passcode=code)
            team_name = preview_team.name
            team_members = preview_team.members
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
                messages.success(request, f"You reconnected to {desired_team.name}.")
                return HttpResponseRedirect(reverse('play'))
            except models.Team.DoesNotExist:
                form.add_error(None, ValidationError('Could not reconnect that team. Check that you have the right ID and code.', code='notfound'))
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
        'team_members': team_members,
    })


def play(request):
    if request.htmx:
        Redirect = HttpResponseClientRedirect
    else:
        Redirect = HttpResponseRedirect

    if 'game' not in request.session:
        _flash_not_in_game(request)
        return Redirect(reverse('home'))
    if 'team' not in request.session:
        _flash_no_team(request)
        return Redirect(reverse('home'))

    config = {
        'game': models.Game.objects.get(pk=request.session['game']),
        'team': models.Team.objects.get(pk=request.session['team']),
    }

    if request.htmx:
        if not config['game'].open:
            # redirects to self, which will render the closed page next time
            return Redirect(reverse('play'))
        
        return render(request, 'game/_page_list.html', config)

    else:
        if not config['game'].open:
            return render(request, 'game/closed.html', config)

        return render(request, 'game/pages.html', config)


def _get_game_team(request, Redirect=HttpResponseRedirect):
    if 'game' not in request.session:
        _flash_not_in_game(request)
        return None, None, Redirect(reverse('home'))

    if 'team' not in request.session:
        _flash_no_team(request)
        return None, None, Redirect(reverse('home'))
    
    try:
        game = models.Game.objects.get(pk=request.session['game'])
    except models.Game.DoesNotExist:
        game = None

    if not game.open:
        _flash_game_not_open(request)
        return game, None, Redirect(reverse('play'))

    try:
        team = models.Team.objects.get(pk=request.session['team'])
    except models.Team.DoesNotExist:
        _flash_no_team(request)
        return game, None, Redirect(reverse('home'))
    
    return game, team, None


def answer_sheet(request, page_order):
    game, team, response = _get_game_team(request)
    if response:
        return response

    try:
        page = game.page_set.get(order=page_order)
        if page.state == models.Page.PageState.LOCKED:
            page = None
    except models.Page.DoesNotExist:
        page = None

    if not page:
        _flash_bad_page(request)
        return HttpResponseRedirect(reverse('play'))

    return render(request, 'game/answer.html', {
        'game': game,
        'team': team,
        'page': page,
    })


def question_hx(request, question_id):
    game, team, response = _get_game_team(request, HttpResponseClientRedirect)
    if response:
        return response

    try:
        question = models.Question.objects.get(pk=question_id)
        if question.page.state == models.Page.PageState.LOCKED:
            question = None
    except models.Question.DoesNotExist:
        question = None

    if not question:
        _flash_bad_question(request)
        return HttpResponseClientRedirect(reverse('play'))
    
    try:
        response = models.Response.objects.get(team=team, question=question)
    except models.Response.DoesNotExist:
        response = None

    did_save = None    
    if request.method == 'POST':
        # page must be accepting answers and existing response,
        # if any, must not be scored yet
        keep_going = True
        did_save = False
        if not question.page.is_open:
            messages.error(request, "This page is not accepting answers now.")
            keep_going = False
        if response and response.graded:
            messages.error(request, f"Your existing response to question {question.order} is already being scored.")
            keep_going = False
        
        new_response = request.POST['response_value']
        
        if keep_going:
            if response:
                response.value = new_response
            else:
                response = models.Response(team=team, question=question, value=new_response)

            response.save()
            did_save = True
    
    return render(request, 'game/_question.html', {
        'game': game,
        'team': team,
        'question': question,
        'response': response,
        'did_save': did_save,
    })


def leaderboard(request):
    if 'game' not in request.session:
        _flash_not_in_game(request)
        return HttpResponseRedirect(reverse('home'))
    if 'team' not in request.session:
        _flash_no_team(request)
        return HttpResponseRedirect(reverse('home'))

    game = models.Game.objects.get(pk=request.session['game'])
    team = models.Team.objects.get(pk=request.session['team'])

    rounds, ldr_board, gold_medals = compute_leaderboard_data(game)

    return render(request, 'game/leaderboard.html', {
        'game': game,
        'team': team,
        'teams': { t.name: t.members for t in game.team_set.all() },
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
    rounds = [
        round.order
        for round in (
            game.page_set
            .exclude(is_hidden=True, state=models.Page.PageState.LOCKED)
        )] + ['total']
    l_board = { t.name: {r: 0 for r in rounds} for t in game.team_set.all() }
    for r in responses:
        try:
            l_board[r.team.name][r.question.page.order] += r.score
            l_board[r.team.name]['total'] += r.score
        except KeyError:
            if r.question.page.order not in l_board[r.team.name]:
                # this is an answer on a hidden page that was re-locked
                # after scoring; it is intentionally omitted
                pass
            else:
                # something else might be going on, and we should fail
                raise
    
    # now we want a list of lists, sorted by total score
    final_board = [[team_name] + list(rest.values()) for team_name, rest in l_board.items()]
    final_board.sort(key=lambda line: line[-1], reverse=True)

    # find first place winners
    gold_medals = []
    if len(final_board) > 0:
        top_score = final_board[0][-1]
        if top_score:
            gold_medals = [line[0] for line in final_board if line[-1] == top_score]

    return rounds, final_board, gold_medals


def _flash_not_in_game(request):
    messages.error(request, "You're not in a game.")

def _flash_no_team(request):
    messages.warning(request, "You don't have a team.")

def _flash_game_not_open(request):
    messages.error(request, "The game isn't open.")

def _flash_bad_page(request):
    messages.error(request, "That's not a page in the game.")

def _flash_bad_question(request):
    messages.error(request, "Question not found or not open.")
